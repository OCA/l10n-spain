import logging
from collections import OrderedDict

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import config

_logger = logging.getLogger(__name__)

VERIFACTU_VALID_POS_STATES = ["paid", "done"]


class PosOrder(models.Model):
    _name = "pos.order"
    _inherit = ["pos.order", "verifactu.mixin"]

    @api.depends(
        "company_id",
        "company_id.verifactu_enabled",
        "company_id.verifactu_start_date",
        "date_order",
        "fiscal_position_id",
        "fiscal_position_id.aeat_active",
        "session_id",
        "session_id.config_id",
        "session_id.config_id.journal_id",
        "session_id.config_id.journal_id.verifactu_enabled",
    )
    def _compute_verifactu_enabled(self):
        """Compute if the POS order is enabled for the veri*FACTU"""
        for order in self:
            # Check if journal is verifactu enabled
            journal_enabled = (
                order.session_id
                and order.session_id.config_id
                and order.session_id.config_id.journal_id
                and order.session_id.config_id.journal_id.verifactu_enabled
            )

            if (
                order.company_id.verifactu_enabled
                and journal_enabled
                and (
                    not order.company_id.verifactu_start_date
                    or order.date_order
                    and order.date_order.date() >= order.company_id.verifactu_start_date
                )
            ):
                order.verifactu_enabled = (
                    order.fiscal_position_id and order.fiscal_position_id.aeat_active
                ) or not order.fiscal_position_id
            else:
                order.verifactu_enabled = False

    @api.depends("fiscal_position_id")
    def _compute_verifactu_tax_key(self):
        for order in self:
            order.verifactu_tax_key = order.fiscal_position_id.verifactu_tax_key or "01"

    @api.depends("fiscal_position_id")
    def _compute_verifactu_registration_key(self):
        for order in self:
            if order.fiscal_position_id:
                key = order.fiscal_position_id.verifactu_registration_key
                if key:
                    order.verifactu_registration_key = key
            else:
                domain = [
                    ("code", "=", "01"),
                    (
                        "verifactu_tax_key",
                        "=",
                        "01",
                    ),
                ]
                verifactu_key_obj = self.env["verifactu.registration.key"]
                order.verifactu_registration_key = verifactu_key_obj.search(
                    domain, limit=1
                )

    @api.model
    def _process_order(self, order, draft, existing_order):
        pos_order_id = super()._process_order(order, draft, existing_order)
        pos_order = self.env["pos.order"].browse(pos_order_id)

        if not pos_order._is_verifactu_order():
            return pos_order_id

        pos_order.verifactu_registration_date = fields.Datetime.now()

        try:
            pos_order._generate_verifactu_chaining()
        except UserError as e:
            # Don't re-raise the error to avoid blocking POS operations
            _logger.error(
                "[ID: %d, REF: %s, INV: %s] Failed to create verifactu chaining: %s",
                pos_order.id,
                pos_order.pos_reference,
                pos_order.l10n_es_unique_id,
                str(e),
            )

        return pos_order_id

    def _is_verifactu_order(self):
        self.ensure_one()
        return self.exists() and not self.to_invoice and self.verifactu_enabled

    def _is_refund_order(self):
        """Check if this POS order is a refund"""
        self.ensure_one()
        return self.amount_total < 0

    def _should_send_to_verifactu(self, pos_order):
        return (
            pos_order._is_verifactu_order()
            and not config["test_enable"]
            and pos_order.state in VERIFACTU_VALID_POS_STATES
        )

    def _get_verifactu_document_type(self):
        if self._is_refund_order():
            return "R5"  # Refund for simplified invoices
        return "F2"  # Regular simplified invoice for POS orders

    def _get_verifactu_description(self):
        return self.verifactu_description or self.company_id.verifactu_description

    def _get_verifactu_chaining(self):
        """Return the verifactu chaining for this POS order.

        For POS orders, we use the company-wide chaining like invoices.
        TODO: Allow the user to setup a new chaining for each PoS Config.
        """
        return self.company_id.verifactu_chaining_id

    def _get_verifactu_previous_hash(self):
        """Get the previous hash from the verifactu invoice entry chain."""
        if self.last_verifactu_invoice_entry_id:
            return self.last_verifactu_invoice_entry_id.previous_hash or ""
        return ""

    def _get_verifactu_registration_date(self):
        """Get the registration date in ISO 8601 format."""
        if not self.verifactu_registration_date:
            return ""
        # Date format must be ISO 8601
        return (
            pytz.utc.localize(self.verifactu_registration_date)
            .astimezone()
            .isoformat(timespec="seconds")
        )

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

    def _verifactu_get_partner(self):
        """Get the partner for AEAT purposes"""
        return (
            self.partner_id.commercial_partner_id
            if self.partner_id
            else self.env["res.partner"]
        )

    @api.depends("amount_total")
    def _compute_verifactu_refund_type(self):
        """Compute refund type for POS orders"""
        for order in self:
            if order._is_refund_order():
                order.verifactu_refund_type = "I"  # By differences
            else:
                order.verifactu_refund_type = False

    def _get_verifactu_qr_values(self):
        """Get the QR values for the verifactu"""
        self.ensure_one()
        _taxes_dict, _amount_tax, amount_total = self._get_verifactu_taxes_and_total()
        return OrderedDict(
            [
                ("nif", self._get_verifactu_issuer()),
                ("numserie", self._get_document_serial_number()),
                (
                    "fecha",
                    self._change_date_format(self._get_document_fiscal_date()),
                ),
                ("importe", f"{amount_total:.2f}"),
            ]
        )

    def _get_verifactu_hash_string(self, cancel=False):
        """Gets the verifactu hash string"""
        if (
            not self.verifactu_enabled
            or self.state not in VERIFACTU_VALID_POS_STATES
            or self.is_invoiced
        ):
            return ""
        issuer = self._get_verifactu_issuer()
        serial_number = self._get_document_serial_number()
        expedition_date = self._change_date_format(self._get_document_date())
        document_type = self._get_verifactu_document_type()
        _taxes_dict, amount_tax, amount_total = self._get_verifactu_taxes_and_total()
        amount_tax = round(amount_tax, 2)
        amount_total = round(amount_total, 2)
        previous_hash = self._get_verifactu_previous_hash()
        registration_date = self._get_verifactu_registration_date()
        verifactu_hash_string = (
            f"IDEmisorFactura={issuer}&"
            f"NumSerieFactura={serial_number}&"
            f"FechaExpedicionFactura={expedition_date}&"
            f"TipoFactura={document_type}&"
            f"CuotaTotal={amount_tax}&"
            f"ImporteTotal={amount_total}&"
            f"Huella={previous_hash}&"
            f"FechaHoraHusoGenRegistro={registration_date}"
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
            "Encadenamiento": self._get_verifactu_chaining_invoice_dict(),
            "SistemaInformatico": self._get_verifactu_developer_dict(),
            "FechaHoraHusoGenRegistro": self._get_verifactu_registration_date(),
            "TipoHuella": "01",  # SHA-256
            "Huella": self.verifactu_hash,
        }

        # Add rectification information for refunds
        if self._is_refund_order():
            inv_dict["TipoRectificativa"] = self.verifactu_refund_type
            # Add reference to original order if available
            if self.refunded_order_ids:
                original_order = self.refunded_order_ids[0]
                inv_dict["FacturasRectificadas"] = [
                    {
                        "IDFacturaRectificada": {
                            "IDEmisorFactura": original_order._get_verifactu_issuer(),
                            "NumSerieFactura": original_order._get_document_serial_number(),
                            "FechaExpedicionFactura": original_order._change_date_format(
                                original_order._get_document_date()
                            ),
                        }
                    }
                ]

        if self.aeat_state in ("sent_w_errors", "incorrect"):
            # en caso de subsanación, debe generar un nuevo hash
            inv_dict["Subsanacion"] = "S"
            if self.aeat_state == "incorrect":
                inv_dict["RechazoPrevio"] = "X"

        registroAlta = {}
        registroAlta.setdefault("RegistroAlta", inv_dict)
        return registroAlta

    def _get_verifactu_chaining_invoice_dict(self):
        """Get the chaining invoice dictionary for POS orders using the new system."""
        if (
            self.last_verifactu_invoice_entry_id
            and self.last_verifactu_invoice_entry_id.previous_invoice_entry_id
        ):
            prev_entry = self.last_verifactu_invoice_entry_id.previous_invoice_entry_id
            prev_document = prev_entry.document
            if prev_document:
                return {
                    "RegistroAnterior": {
                        "IDEmisorFactura": prev_document._get_verifactu_issuer(),
                        "NumSerieFactura": prev_document._get_document_serial_number(),
                        "FechaExpedicionFactura": prev_document._change_date_format(
                            prev_document._get_document_date()
                        ),
                        "Huella": self._get_verifactu_previous_hash(),
                    }
                }
        return {"PrimerRegistro": "S"}

    def _get_verifactu_receiver_dict(self):
        """Get receiver dict for POS orders."""
        self.ensure_one()
        partner = self._verifactu_get_partner()
        if not partner:
            return {}
        return {
            "NombreRazon": partner.name,
            "NIF": partner._parse_aeat_vat_info()[2] if partner.vat else "",
        }

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
        taxes_RE = self._get_verifactu_taxes_map(["RE"], document_date)
        taxes_not_in_total = self._get_verifactu_taxes_map(
            ["TaxNotIncludedInTotal"], document_date
        )
        base_not_in_total = self._get_verifactu_taxes_map(
            ["BaseNotIncludedInTotal"], document_date
        )
        excluded_taxes = taxes_not_in_total + base_not_in_total
        breakdown_taxes = taxes_S1 + taxes_S2 + taxes_N1 + taxes_N2
        not_in_amount_total = 0.0
        not_in_taxes = 0.0

        # Build tax breakdown
        for tax_line in tax_lines.values():
            tax = tax_line["tax"]
            if tax in taxes_not_in_total:
                not_in_amount_total += tax_line["amount"]
            elif tax in base_not_in_total:
                not_in_amount_total += tax_line["base"]
            if tax in breakdown_taxes:
                operation_type = self._get_verifactu_operation_type(
                    tax_line, taxes_S1, taxes_S2, taxes_N1, taxes_N2
                )
                tax_dict = {
                    "Impuesto": self.verifactu_tax_key,
                    "ClaveRegimen": self.verifactu_registration_key_code,
                    "CalificacionOperacion": operation_type,
                }
                if operation_type not in ("N1", "N2"):
                    new_tax_dict = self._get_verifactu_tax_dict(tax_line, tax_lines)
                    tax_dict.update(new_tax_dict)
                else:
                    tax_dict.update({"BaseImponibleOimporteNoSujeto": tax_line["base"]})
                taxes_dict["DetalleDesglose"].append(tax_dict)
            elif tax in excluded_taxes:
                not_in_taxes += tax_line["amount"]
            elif tax not in taxes_RE:
                raise UserError(_("%s tax is not mapped to VERI*FACTU.", tax.name))
        sign = -1 if self._is_refund_order() else 1
        amount_tax = self.amount_tax - not_in_taxes * sign
        amount_total = self.amount_total - not_in_amount_total
        return (
            taxes_dict,
            amount_tax,
            amount_total,
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

    def _get_verifactu_operation_type(
        self, tax_line, taxes_S1, taxes_S2, taxes_N1, taxes_N2
    ):
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

    def resend_verifactu(self):
        """Resend POS orders to verifactu after errors"""
        for order in self:
            if (
                order.aeat_state in ("sent_w_errors", "incorrect")
                and order.last_verifactu_invoice_entry_id
                and not order.last_verifactu_invoice_entry_id.send_state == "not_sent"
            ):
                entry_type = (
                    "modify" if order.aeat_state == "sent_w_errors" else "register"
                )
                order.verifactu_registration_date = fields.Datetime.now()
                order._generate_verifactu_chaining(entry_type=entry_type)

    def _check_verifactu_configuration(self):
        """Check POS order configuration for verifactu"""
        if not self.fiscal_position_id:
            raise UserError(
                _(
                    "[ID: %(id)d, REF: %(ref)s, INV: %(inv)s] The POS order cannot be sent to "
                    "Verifactu because it does not have a fiscal position."
                )
                % {
                    "id": self.id,
                    "ref": self.pos_reference,
                    "inv": self.l10n_es_unique_id,
                }
            )
        if not self.verifactu_tax_key:
            raise UserError(
                _(
                    "[ID: %(id)d, REF: %(ref)s, INV: %(inv)s] The POS order cannot be sent to "
                    "Verifactu because it does not have a tax key."
                )
                % {
                    "id": self.id,
                    "ref": self.pos_reference,
                    "inv": self.l10n_es_unique_id,
                }
            )
        if not self.verifactu_registration_key:
            raise UserError(
                _(
                    "[ID: %(id)d, REF: %(ref)s, INV: %(inv)s] The POS order cannot be sent to "
                    "Verifactu because it does not have a registration key."
                )
                % {
                    "id": self.id,
                    "ref": self.pos_reference,
                    "inv": self.l10n_es_unique_id,
                }
            )

        if not self._check_inconsistent_taxes():
            raise UserError(
                _(
                    "[ID: %(id)d, REF: %(ref)s, INV: %(inv)s] The POS order cannot be sent to "
                    "Verifactu because there are some inconsistent taxes on lines."
                )
                % {
                    "id": self.id,
                    "ref": self.pos_reference,
                    "inv": self.l10n_es_unique_id,
                }
            )

        if not self._check_all_taxes_mapped():
            raise UserError(
                _(
                    "[ID: %(id)d, REF: %(ref)s, INV: %(inv)s] The POS order cannot be sent to "
                    "Verifactu because it does not have all taxes mapped."
                )
                % {
                    "id": self.id,
                    "ref": self.pos_reference,
                    "inv": self.l10n_es_unique_id,
                }
            )
        return super()._check_verifactu_configuration()

    def _check_inconsistent_taxes(self):
        """Check for inconsistent taxes on POS order lines"""
        document_date = self._get_document_fiscal_date()
        taxes_S1 = self._get_verifactu_taxes_map(["S1"], document_date)
        taxes_S2 = self._get_verifactu_taxes_map(["S2"], document_date)
        taxes_RE = self._get_verifactu_taxes_map(["RE"], document_date)

        for line in self.lines:
            taxes_in_s1 = line.tax_ids_after_fiscal_position.filtered(
                lambda x: x in taxes_S1
            )
            if len(taxes_in_s1) > 1:
                return False
            taxes_in_s2 = line.tax_ids_after_fiscal_position.filtered(
                lambda x: x in taxes_S2
            )
            if len(taxes_in_s2) > 1:
                return False
            taxes_in_RE = line.tax_ids_after_fiscal_position.filtered(
                lambda x: x in taxes_RE
            )
            if len(taxes_in_RE) > 1:
                return False
        return True

    def _check_all_taxes_mapped(self):
        """Check if all taxes used in POS order are mapped to verifactu"""
        # Get all taxes used in the order
        all_taxes = self.env["account.tax"]
        for line in self.lines:
            all_taxes |= line.tax_ids_after_fiscal_position

        if not all_taxes:
            raise UserError(
                _(
                    "The POS order %s cannot be sent to Verifactu because"
                    "it does not have any taxes."
                )
                % self.pos_reference
            )

        document_date = self._get_document_fiscal_date()
        verifactu_map = self._get_verifactu_map(document_date)
        tax_templates = verifactu_map.map_lines.mapped("taxes")
        mapped_taxes = self.company_id.get_taxes_from_templates(tax_templates)

        for tax in all_taxes:
            if tax not in mapped_taxes:
                return False
        return True

    def cancel_verifactu(self):
        """Cancel POS order on verifactu - not implemented"""
        raise NotImplementedError

    def write(self, vals):
        """Override write to protect fields once sent to verifactu"""
        PROTECTED_FIELDS = {
            "date_order": _("order date"),
            "pos_reference": _("POS reference"),
            "l10n_es_unique_id": _("simplified invoice number"),
        }

        modified_protected = set(vals.keys()) & set(PROTECTED_FIELDS.keys())
        if modified_protected:
            for order in self.filtered(
                lambda x: x.verifactu_enabled and x.aeat_state != "not_sent"
            ):
                protected_field_names = [
                    PROTECTED_FIELDS[field] for field in modified_protected
                ]
                raise UserError(
                    _(
                        "[ID: %(id)d, REF: %(ref)s, INV: %(inv)s] "
                        "You cannot change the %(fields)s "
                        "of document already registered at VERI*FACTU. You must cancel the "
                        "document and create a new one with the correct value."
                    )
                    % {
                        "id": order.id,
                        "ref": order.pos_reference,
                        "inv": order.l10n_es_unique_id,
                        "fields": ", ".join(protected_field_names),
                    }
                )

        return super().write(vals)
