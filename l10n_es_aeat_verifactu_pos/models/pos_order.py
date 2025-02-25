import logging
from collections import OrderedDict
from time import sleep

import pytz
from psycopg2 import OperationalError

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import config

_logger = logging.getLogger(__name__)

VERIFACTU_VALID_POS_STATES = [
    "paid",  # paid is set on PoS order processing
    "done",  # done is set on PoS session validation (closing)
]

# TODO: move to l10n_es_aeat_verifactu
SEND_TO_VERIFACTU_MAX_RETRIES = 5


class PosOrder(models.Model):
    _name = "pos.order"
    _inherit = ["pos.order", "verifactu.mixin"]

    verifactu_previous_invoice_id = fields.Many2one(
        string="Previous veri*FACTU Order sent",
        comodel_name="pos.order",
        copy=False,
    )

    @api.depends("amount_total")
    def _compute_verifactu_macrodata(self):
        return super()._compute_verifactu_macrodata()

    @api.depends(
        "company_id",
        "company_id.verifactu_enabled",
        "fiscal_position_id",
        "fiscal_position_id.aeat_active",
    )
    def _compute_verifactu_enabled(self):
        """Compute if the POS order is enabled for the veri*FACTU"""
        for order in self:
            if order.company_id.verifactu_enabled:
                order.verifactu_enabled = (
                    order.fiscal_position_id and order.fiscal_position_id.aeat_active
                ) or not order.fiscal_position_id
            else:
                order.verifactu_enabled = False

    @api.model
    def _process_order(self, order, draft, existing_order):
        pos_order_id = super()._process_order(order, draft, existing_order)
        pos_order = self.env["pos.order"].browse(pos_order_id)

        if not self._is_verifactu_order(pos_order):
            return pos_order_id

        # TODO: review retry strategy
        # possible scenarios: multiple devices registering invoices
        # from the same PoS Config
        for attempt in range(SEND_TO_VERIFACTU_MAX_RETRIES):
            try:
                pos_order._set_chaining_invoice()
                break
            except OperationalError:
                if attempt == SEND_TO_VERIFACTU_MAX_RETRIES - 1:
                    # TODO: should we have a stopping mechanism and avoid sending more
                    # invoices for this chain when it is no possible to obtain a lock
                    # on verifactu_last_invoice_id (pos.config)?
                    _logger.error(
                        "Failed to send order %s with ID %d to Verifactu after %d attempts",
                        pos_order.l10n_es_unique_id,
                        pos_order.id,
                        SEND_TO_VERIFACTU_MAX_RETRIES,
                    )
                    raise
                else:
                    sleep(1)  # Wait 1 second before next try

        if self._should_send_to_verifactu(pos_order):
            pos_order.send_verifactu()

        return pos_order_id

    def _is_verifactu_order(self, pos_order):
        return (
            pos_order.exists()
            and not pos_order.to_invoice
            and pos_order.verifactu_enabled
        )

    def _should_send_to_verifactu(self, pos_order):
        return (
            self._is_verifactu_order(pos_order)
            and not config["test_enable"]
            and pos_order.state in VERIFACTU_VALID_POS_STATES
        )

    def _get_verifactu_document_type(self):
        return "F2"  # Simplified invoice for POS orders

    def _get_verifactu_description(self):
        return self.verifactu_description or self.company_id.verifactu_description

    def _get_document_date(self):
        return self.date_order

    def _get_document_fiscal_date(self):
        return self.date_order

    def _get_valid_document_states(self):
        return VERIFACTU_VALID_POS_STATES

    def _get_document_serial_number(self):
        return (self.l10n_es_unique_id or self.pos_reference)[0:60]

    def _get_mapping_key(self):
        return "out_invoice"

    def _get_verifactu_issuer(self):
        return self.company_id.partner_id._parse_aeat_vat_info()[2]

    def _get_verifactu_amount_tax(self):
        return self.amount_tax

    def _get_verifactu_amount_total(self):
        return self.amount_total

    def _get_verifactu_previous_hash(self):
        return self.verifactu_previous_invoice_id.verifactu_hash

    def _get_verifactu_registration_date(self):
        return (
            pytz.utc.localize(self.create_date)
            .astimezone()
            .isoformat(timespec="seconds")
        )

    def _get_verifactu_qr_values(self):
        """Get the QR values for the verifactu"""
        self.ensure_one()
        return OrderedDict(
            [
                ("nif", self._get_verifactu_issuer()),
                ("numserie", self._get_document_serial_number()),
                (
                    "fecha",
                    self._change_date_format(self._get_document_fiscal_date()),
                ),
                ("importe", self._get_verifactu_amount_total()),
            ]
        )

    def _get_verifactu_hash_string(self):
        """Gets the verifactu hash string"""
        if (
            not self.verifactu_enabled
            or self.state not in VERIFACTU_VALID_POS_STATES
            or self.is_invoiced
        ):
            return ""
        issuerID = self._get_verifactu_issuer()
        serialNumber = self._get_document_serial_number()
        expeditionDate = self._change_date_format(self._get_document_date())
        documentType = self._get_verifactu_document_type()
        amountTax = self._get_verifactu_amount_tax()
        amountTotal = self._get_verifactu_amount_total()
        previousHash = self._get_verifactu_previous_hash()
        registrationDate = self._get_verifactu_registration_date()
        verifactu_hash_string = (
            f"IDEmisorFactura={issuerID}&"
            f"NumSerieFactura={serialNumber}&"
            f"FechaExpedicionFactura={expeditionDate}&"
            f"TipoFactura={documentType}&"
            f"CuotaTotal={amountTax}&"
            f"ImporteTotal={amountTotal}&"
            f"Huella={previousHash}&"
            f"FechaHoraHusoGenRegistro={registrationDate}"
        )
        return verifactu_hash_string

    def _get_verifactu_invoice_dict_out(self, cancel=False):
        """Build dict with data to send to AEAT WS for POS orders."""
        self.ensure_one()
        document_date = self._change_date_format(self._get_document_date())
        company = self.company_id
        serial_number = self._get_document_serial_number()
        taxes_dict, amount_tax, amount_total = self._get_verifactu_taxes_and_total()
        company_vat = company.partner_id._parse_aeat_vat_info()[2]
        verifactu_doc_type = self._get_verifactu_document_type()
        registroAlta = {}
        inv_dict = {
            "IDVersion": self._get_verifactu_version(),
            "IDFactura": {
                "IDEmisorFactura": company_vat,
                "NumSerieFactura": serial_number,
                "FechaExpedicionFactura": document_date,
            },
            "NombreRazonEmisor": self.company_id.name[0:120],
            "TipoFactura": verifactu_doc_type,
            "DescripcionOperacion": self._get_verifactu_description(),
            "Desglose": taxes_dict,
            "CuotaTotal": amount_tax,
            "ImporteTotal": amount_total,
            "Encadenamiento": self._get_chaining_invoice_dict(),
            "SistemaInformatico": self._get_verifactu_developer_dict(),
            "FechaHoraHusoGenRegistro": self._get_verifactu_registration_date(),
            "TipoHuella": "01",  # SHA-256
            "Huella": self.verifactu_hash,
        }
        registroAlta.setdefault("RegistroAlta", inv_dict)
        return registroAlta

    def _set_chaining_invoice(self):
        """Set the chaining order"""
        prev_order = False
        try:
            self.config_id.flush_model(["verifactu_last_invoice_id"])
            self._cr.execute(
                "SELECT verifactu_last_invoice_id FROM"
                " pos_config WHERE id = %s FOR UPDATE NOWAIT",
                [self.config_id.id],
            )
            result = self._cr.fetchone()
            prev_order = self.env["pos.order"].browse(result[0]) if result else False
            if prev_order and prev_order.exists():
                self.verifactu_previous_invoice_id = prev_order
            self._cr.execute(
                "UPDATE pos_config SET verifactu_last_invoice_id = %s WHERE id = %s",
                (self.id, self.config_id.id),
            )
            self.config_id.invalidate_recordset(["verifactu_last_invoice_id"])
        except OperationalError:
            _logger.error(
                "VERI*FACTU: Could not obtain lock for PoS Config %s "
                "and order %s with ID %d",
                self.config_id.id,
                self.l10n_es_unique_id,
                self.id,
            )
            raise
        return prev_order

    def _get_chaining_invoice_dict(self):
        """Get the chaining invoice dictionary for POS orders"""
        if self.verifactu_previous_invoice_id:
            prev_order = self.verifactu_previous_invoice_id
            return {
                "RegistroAnterior": {
                    "IDEmisorFactura": prev_order._get_verifactu_issuer(),
                    "NumSerieFactura": prev_order._get_document_serial_number(),
                    "FechaExpedicionFactura": prev_order._change_date_format(
                        prev_order._get_document_date()
                    ),
                    "Huella": prev_order.verifactu_hash,
                }
            }
        return {"PrimerRegistro": "S"}

    def _get_verifactu_taxes_and_total(self):
        """Get the tax breakdown for Verifactu from POS order lines.

        Returns:
            tuple: (taxes_dict, amount_tax, amount_total) where:
                - taxes_dict: Dictionary with tax breakdown
                - amount_tax: Total tax amount
                - amount_total: Total amount with taxes
        """
        self.ensure_one()
        taxes_dict = {}
        taxes_dict.setdefault("DetalleDesglose", [])

        # Get tax lines from POS order
        tax_lines = {}
        for line in self.lines:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_ids_after_fiscal_position.compute_all(
                price,
                self.pricelist_id.currency_id,
                line.qty,
                product=line.product_id,
                partner=self.partner_id or False,
            )

            for tax_vals in taxes["taxes"]:
                tax = self.env["account.tax"].browse(tax_vals["id"])
                if tax not in tax_lines:
                    tax_lines[tax] = {
                        "tax": tax,
                        "base": tax_vals["base"],
                        "amount": tax_vals["amount"],
                    }
                else:
                    tax_lines[tax]["base"] += tax_vals["base"]
                    tax_lines[tax]["amount"] += tax_vals["amount"]

        # Get tax mappings
        document_date = self._get_document_fiscal_date()
        taxes_S1 = self._get_verifactu_taxes_map(["S1"], document_date)
        taxes_S2 = self._get_verifactu_taxes_map(["S2"], document_date)
        taxes_N1 = self._get_verifactu_taxes_map(["N1"], document_date)
        taxes_N2 = self._get_verifactu_taxes_map(["N2"], document_date)
        breakdown_taxes = taxes_S1 + taxes_S2 + taxes_N1 + taxes_N2

        # Build tax breakdown
        for tax_line in tax_lines.values():
            tax = tax_line["tax"]
            if tax in breakdown_taxes:
                operation_type = self._get_operation_type(
                    tax_line, taxes_S1, taxes_S2, taxes_N1, taxes_N2
                )
                tax_dict = {
                    "Impuesto": self.verifactu_tax_key,
                    "ClaveRegimen": self.verifactu_registration_key_code,
                    "CalificacionOperacion": operation_type,
                }
                tax_dict.update(self._get_verifactu_tax_dict(tax_line, tax_lines))
                taxes_dict["DetalleDesglose"].append(tax_dict)

        return (
            taxes_dict,
            self._get_verifactu_amount_tax(),
            self._get_verifactu_amount_total(),
        )

    def _get_verifactu_tax_dict(self, tax_line, tax_lines):
        """Get the Verifactu tax dictionary for the passed tax line.

        Args:
            tax_line (dict): Tax line being analyzed
            tax_lines (dict): Dictionary of processed taxes

        Returns:
            dict: Verifactu tax values
        """
        tax = tax_line["tax"]
        tax_base_amount = tax_line["base"]
        if tax.amount_type == "group":
            tax_type = abs(tax.children_tax_ids.filtered("amount")[:1].amount)
        else:
            tax_type = abs(tax.amount)

        tax_dict = {
            "TipoImpositivo": str(tax_type),
            "BaseImponibleOimporteNoSujeto": tax_base_amount,
            "CuotaRepercutida": tax_line["amount"],
        }

        # Recargo de equivalencia
        req_tax = self._get_verifactu_tax_req(tax)
        if req_tax:
            tax_dict["TipoRecargoEquivalencia"] = req_tax.amount
            tax_dict["CuotaRecargoEquivalencia"] = tax_lines[req_tax]["amount"]

        return tax_dict

    def _get_verifactu_tax_req(self, tax):
        """Get the associated req tax for the specified tax.

        Args:
            tax: Initial tax for searching RE linked tax

        Returns:
            account.tax: REQ tax linked to provided tax

        Raises:
            UserError: If there's a mismatch in RE taxes
        """
        self.ensure_one()
        document_date = self._get_document_fiscal_date()
        taxes_req = self._get_verifactu_taxes_map(["RE"], document_date)

        re_lines = self.lines.filtered(
            lambda x: tax in x.tax_ids and x.tax_ids & taxes_req
        )
        req_tax = re_lines.mapped("tax_ids") & taxes_req

        if len(req_tax) > 1:
            raise UserError(_("There's a mismatch in taxes for RE. Check them."))
        return req_tax

    def _get_operation_type(self, tax_line, taxes_S1, taxes_S2, taxes_N1, taxes_N2):
        """Get the operation type for Verifactu based on tax configuration.

        Args:
            tax_line (dict): Tax line info
            taxes_S1: Taxes for type S1
            taxes_S2: Taxes for type S2
            taxes_N1: Taxes for type N1
            taxes_N2: Taxes for type N2

        Returns:
            str: Operation type code (S1, S2, N1, N2)
        """
        tax = tax_line["tax"]
        if tax in taxes_S1:
            return "S1"
        elif tax in taxes_S2:
            return "S2"
        elif tax in taxes_N1:
            return "N1"
        elif tax in taxes_N2:
            return "N2"
        return "S1"

    def cancel_verifactu(self):
        raise NotImplementedError
