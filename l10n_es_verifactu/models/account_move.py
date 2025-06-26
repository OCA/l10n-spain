# Copyright 2024 Aures TIC - Almudena de La Puente <almudena@aurestic.es>
# Copyright 2024 Aures Tic - Jose Zambudio <jose@aurestic.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from collections import OrderedDict
from datetime import datetime
from hashlib import sha256

import psycopg2
import pytz

from odoo import _, api, fields, models
from odoo.exceptions import UserError

VERIFACTU_VALID_INVOICE_STATES = ["posted"]


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "verifactu.mixin"]

    verifactu_refund_specific_invoice_type = fields.Selection(
        selection=[
            (
                "R1",
                _("FACTURA RECTIFICATIVA (Art 80.1 y 80.2 y error fundado en derecho)"),
            ),
            ("R2", _("FACTURA RECTIFICATIVA (Art. 80.3)")),
            ("R3", _("FACTURA RECTIFICATIVA (Art. 80.4)")),
            ("R4", _("FACTURA RECTIFICATIVA (Resto)")),
            ("R5", _("FACTURA RECTIFICATIVA EN FACTURAS SIMPLIFICADAS")),
        ],
        help="Fill this field when the refund are one of the specific cases"
        " of article 80 of LIVA for notifying to Vertifactu with the proper"
        " invoice type.",
    )
    verifactu_registration_date = fields.Datetime(copy=False)
    verifactu_registration_key = fields.Many2one(
        comodel_name="verifactu.registration.keys",
        compute="_compute_verifactu_registration_key",
        store=True,
        readonly=False,
    )
    verifactu_tax_key = fields.Selection(
        compute="_compute_verifactu_tax_key",
        store=True,
        readonly=False,
    )
    verifactu_registration_key_code = fields.Char(
        compute="_compute_verifactu_registration_key_code",
        readonly=True,
    )
    verifactu_send_queue_ids = fields.One2many(
        "verifactu.send.queue", "move_id", string="Verifactu Send Queue"
    )
    verifactu_send_response_ids = fields.One2many(
        "verifactu.send.response.line",
        "move_id",
        string="Verifactu Send Response Lines",
    )

    @api.depends("move_type")
    def _compute_verifactu_refund_type(self):
        for record in self:
            if record.move_type == "out_refund":
                record.verifactu_refund_type = "I"
            else:
                record.verifactu_refund_type = False

    @api.depends("amount_total")
    def _compute_verifactu_macrodata(self):
        return super()._compute_verifactu_macrodata()

    @api.depends(
        "company_id",
        "company_id.verifactu_enabled",
        "company_id.verifactu_start_date",
        "invoice_date",
        "move_type",
        "fiscal_position_id",
        "fiscal_position_id.aeat_active",
        "journal_id",
        "journal_id.verifactu_enabled",
    )
    def _compute_verifactu_enabled(self):
        """Compute if the invoice is enabled for the veri*FACTU"""
        for invoice in self:
            if (
                invoice.company_id.verifactu_enabled
                and invoice.journal_id.verifactu_enabled
                and invoice.move_type in ["out_invoice", "out_refund"]
            ) and (
                not invoice.company_id.verifactu_start_date
                or invoice.invoice_date
                and invoice.invoice_date >= invoice.company_id.verifactu_start_date
            ):
                invoice.verifactu_enabled = (
                    invoice.fiscal_position_id
                    and invoice.fiscal_position_id.aeat_active
                ) or not invoice.fiscal_position_id
            else:
                invoice.verifactu_enabled = False

    @api.depends("fiscal_position_id")
    def _compute_verifactu_tax_key(self):
        for document in self:
            document.verifactu_tax_key = (
                document.fiscal_position_id.verifactu_tax_key or "01"
            )

    @api.depends("fiscal_position_id")
    def _compute_verifactu_registration_key(self):
        for document in self:
            if document.fiscal_position_id:
                key = document.fiscal_position_id.verifactu_registration_key
                if key:
                    document.verifactu_registration_key = key
            else:
                domain = [
                    ("code", "=", "01"),
                    (
                        "verifactu_tax_key",
                        "=",
                        "01",
                    ),
                ]
                verifactu_key_obj = self.env["verifactu.registration.keys"]
                document.verifactu_registration_key = verifactu_key_obj.search(
                    domain, limit=1
                )

    @api.depends("verifactu_registration_key")
    def _compute_verifactu_registration_key_code(self):
        for record in self:
            record.verifactu_registration_key_code = (
                record.verifactu_registration_key.code
            )

    def _get_verifactu_document_type(self):
        invoice_type = ""
        if self.move_type in ["out_invoice", "out_refund"]:
            is_simplified = self._is_aeat_simplified_invoice()
            invoice_type = "F2" if is_simplified else "F1"
            if self.move_type == "out_refund":
                if self.verifactu_refund_specific_invoice_type:
                    invoice_type = self.verifactu_refund_specific_invoice_type
                else:
                    invoice_type = "R5" if is_simplified else "R1"
        return invoice_type

    def _get_verifactu_description(self):
        return self.verifactu_description or self.company_id.verifactu_description

    def _get_document_date(self):
        """
        TODO: this method is the same in l10n_es_aeat_sii_oca, so I think that
        it should be directly in l10n_es_aeat
        """
        return self.invoice_date

    def _aeat_get_partner(self):
        """
        TODO: this method is the same in l10n_es_aeat_sii_oca, so I think that
        it should be directly in l10n_es_aeat
        """
        return self.commercial_partner_id

    def _get_document_fiscal_date(self):
        """
        TODO: this method is the same in l10n_es_aeat_sii_oca, so I think that
        it should be directly in l10n_es_aeat
        """
        return self.invoice_date

    def _get_mapping_key(self):
        """
        TODO: this method is the same in l10n_es_aeat_sii_oca, so I think that
        it should be directly in l10n_es_aeat
        """
        return self.move_type

    def _get_verifactu_valid_document_states(self):
        return VERIFACTU_VALID_INVOICE_STATES

    def _get_document_serial_number(self):
        """
        TODO: this method is the same in l10n_es_aeat_sii_oca, so I think that
        it should be directly in l10n_es_aeat
        """
        serial_number = (self.name or "")[0:60]
        if self.thirdparty_invoice:
            serial_number = self.thirdparty_number[0:60]
        return serial_number

    def _get_verifactu_issuer(self):
        return self.company_id.partner_id._parse_aeat_vat_info()[2]

    def _get_verifactu_previous_hash(self):
        if self.verifactu_previous_document_id:
            return self.verifactu_previous_document_id.verifactu_hash
        return ""

    def _get_verifactu_registration_date(self):
        # Date format must be ISO 8601
        return (
            pytz.utc.localize(self.verifactu_registration_date)
            .astimezone()
            .isoformat(timespec="seconds")
        )

    def _get_verifactu_hash_string(self):
        """Gets the verifactu hash string"""
        if (
            not self.verifactu_enabled
            or self.state == "draft"
            or self.move_type not in ("out_invoice", "out_refund")
        ):
            return ""
        issuerID = self._get_verifactu_issuer()
        serialNumber = self._get_document_serial_number()
        expeditionDate = self._change_date_format(self._get_document_date())
        documentType = self._get_verifactu_document_type()
        _taxes_dict, amount_tax, amount_total = self._get_verifactu_taxes_and_total()
        amountTax = round(amount_tax, 2)
        amountTotal = round(amount_total, 2)
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

    @api.model
    def _set_subsanation_verifactu_hash(self):
        verifactu_hash_values = self._get_verifactu_hash_string()
        hash_string = sha256(verifactu_hash_values.encode("utf-8"))
        self.verifactu_hash_string = hash_string
        self.verifactu_hash = hash_string.hexdigest().upper()
        return self.verifactu_hash

    def _get_verifactu_invoice_dict_out(self, cancel=False):
        """Build dict with data to send to AEAT WS for document types:
        out_invoice and out_refund.

        :param cancel: It indicates if the dictionary is for sending a
          cancellation of the document.
        :return: documents (dict) : Dict XML with data for this document.
        """
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
        }
        if self.move_type == "out_refund":
            inv_dict["TipoRectificativa"] = self.verifactu_refund_type
            if self.verifactu_refund_type == "I":
                inv_dict["FacturasRectificadas"] = []
                origin = self.reversed_entry_id
                if origin:
                    orig_document_date = self._change_date_format(
                        origin._get_document_date()
                    )
                    orig_serial_number = origin._get_document_serial_number()
                    origin_data = {
                        "IDFacturaRectificada": {
                            "IDEmisorFactura": company_vat,
                            "NumSerieFactura": orig_serial_number,
                            "FechaExpedicionFactura": orig_document_date,
                        }
                    }
                    inv_dict["FacturasRectificadas"].append(origin_data)
                # inv_dict["ImporteRectificacion"] = {
                #     "BaseRectificada": abs(origin.amount_untaxed_signed),
                #     "CuotaRectificada": abs(
                #         origin.amount_total_signed - origin.amount_untaxed_signed
                #     ),
                # }
        inv_dict.update(
            {
                "DescripcionOperacion": self._get_verifactu_description(),
            }
        )
        if verifactu_doc_type not in ("F2", "R5"):
            inv_dict.update(
                {
                    "Destinatarios": self._get_verifactu_receiver_dict(),
                }
            )
        elif verifactu_doc_type in ("F2", "R5"):
            inv_dict.update({"FacturaSinIdentifDestinatarioArt61d": "S"})
        inv_dict.update(
            {
                "Desglose": taxes_dict,
                "CuotaTotal": amount_tax,
                "ImporteTotal": amount_total,
                "Encadenamiento": self._get_verifactu_chaining_invoice_dict(),
                "SistemaInformatico": self._get_verifactu_developer_dict(),
                "FechaHoraHusoGenRegistro": self._get_verifactu_registration_date(),
                "TipoHuella": "01",  # SHA-256
                "Huella": self.verifactu_hash,
            }
        )
        if self.verifactu_send_state in ["incorrect", "accepted_with_errors"]:
            inv_dict.update(
                {
                    "Subsanacion": "S",
                    "Huella": self._set_subsanation_verifactu_hash(),
                }
            )
        registroAlta.setdefault("RegistroAlta", inv_dict)
        return registroAlta

    def _get_verifactu_chaining_invoice_dict(self):
        prev_document = self.verifactu_previous_document_id
        if prev_document:
            return {
                "RegistroAnterior": {
                    "IDEmisorFactura": prev_document._get_verifactu_issuer(),
                    "NumSerieFactura": prev_document._get_document_serial_number(),
                    "FechaExpedicionFactura": prev_document._change_date_format(
                        prev_document._get_document_date()
                    ),
                    "Huella": prev_document.verifactu_hash,
                }
            }
        return {"PrimerRegistro": "S"}

    def _get_verifactu_tax_dict(self, tax_line, tax_lines):
        """Get the Verifactu tax dictionary for the passed tax line.

        :param self: Single invoice record.
        :param tax_line: Tax line that is being analyzed.
        :param tax_lines: Dictionary of processed invoice taxes for further operations
            (like REQ).
        :return: A dictionary with the corresponding Verifactu tax values.
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
        }
        key = "CuotaRepercutida"
        tax_dict[key] = tax_line["amount"]
        # Recargo de equivalencia
        req_tax = self._get_verifactu_tax_req(tax)
        if req_tax:
            tax_dict["TipoRecargoEquivalencia"] = req_tax.amount
            tax_dict["CuotaRecargoEquivalencia"] = tax_lines[req_tax]["amount"]
        return tax_dict

    def _get_verifactu_tax_dict_ns(self, tax_line):
        """Get the Verifactu tax dictionary for the passed tax line.

        :param self: Single invoice record.
        :param tax_line: Tax line that is being analyzed.
        :return: A dictionary with the corresponding Verifactu tax values.
        """
        tax_base_amount = tax_line["base"]
        tax_dict = {
            "BaseImponibleOimporteNoSujeto": tax_base_amount,
        }
        return tax_dict

    def _get_verifactu_tax_req(self, tax):
        """Get the associated req tax for the specified tax.

        :param self: Single invoice record.
        :param tax: Initial tax for searching for the RE linked tax.
        :return: REQ tax (or empty recordset) linked to the provided tax.
        """
        self.ensure_one()
        document_date = self._get_document_fiscal_date()
        taxes_req = self._get_verifactu_taxes_map(["RE"], document_date)
        re_lines = self.line_ids.filtered(
            lambda x: tax in x.tax_ids and x.tax_ids & taxes_req
        )
        req_tax = re_lines.mapped("tax_ids") & taxes_req
        if len(req_tax) > 1:
            raise UserError(_("There's a mismatch in taxes for RE. Check them."))
        return req_tax

    def _get_verifactu_taxes_and_total(self):
        self.ensure_one()
        taxes_dict = {}
        taxes_dict.setdefault("DetalleDesglose", [])
        tax_lines = self._get_aeat_tax_info()
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
                # si es exenta:
                # "OperacionExenta": "", # TODO
                if operation_type not in ("N1", "N2"):
                    tax_dict.update(self._get_verifactu_tax_dict(tax_line, tax_lines))
                else:
                    tax_dict.update(self._get_verifactu_tax_dict_ns(tax_line))
                taxes_dict["DetalleDesglose"].append(tax_dict)
            elif tax in excluded_taxes:
                not_in_taxes += tax_line["amount"]
            elif tax not in taxes_RE:
                raise UserError(_("%s tax is not mapped to Verifactu." % tax.name))
        amount_tax = self.amount_tax_signed - not_in_taxes
        amount_total = self.amount_total_signed - not_in_amount_total
        return (
            taxes_dict,
            amount_tax,
            amount_total,
        )

    def _get_verifactu_operation_type(
        self, tax_line, taxes_S1, taxes_S2, taxes_N1, taxes_N2
    ):
        """
        S1	Operación Sujeta y No exenta - Sin inversión del sujeto pasivo.
        S2	Operación Sujeta y No exenta - Con Inversión del sujeto pasivo
        N1	Operación No Sujeta artículo 7, 14, otros.
        N2	Operación No Sujeta por Reglas de localización.
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

    def _get_verifactu_receiver_dict(self):
        self.ensure_one()
        receiver = self._aeat_get_partner()
        (
            country_code,
            identifier_type,
            identifier,
        ) = receiver._parse_aeat_vat_info()
        if identifier:
            identifier = "".join(e for e in identifier if e.isalnum()).upper()
        else:
            identifier = "NO_DISPONIBLE"
            identifier_type = "06"
        if identifier_type == "":
            return {
                "IDDestinatario": {
                    "NombreRazon": receiver.name,
                    "NIF": identifier,
                }
            }
        return {
            "IDDestinatario": {
                "NombreRazon": receiver.name,
                "IDOtro": {
                    "CodigoPais": receiver.country_id.code,
                    "IDType": identifier_type,
                    "ID": country_code,
                },
            }
        }

    def _get_verifactu_qr_values(self):
        """Get the QR values for the verifactu"""
        self.ensure_one()
        company_vat = self.company_id.partner_id._parse_aeat_vat_info()[2]
        _taxes_dict, _amount_tax, amount_total = self._get_verifactu_taxes_and_total()
        return OrderedDict(
            [
                ("nif", company_vat),
                ("numserie", self.name),
                ("fecha", self.invoice_date.strftime("%d-%m-%Y")),
                ("importe", amount_total),
            ]
        )

    def _post(self, soft=True):
        res = super()._post(soft=soft)
        for record in self:
            if record.verifactu_enabled and record.verifactu_send_state == "not_sent":
                record._check_verifactu_configuration()
                record.verifactu_registration_date = datetime.now()
                record._generate_verifactu_chaining()
                self.env["verifactu.send.queue"].sudo().create(
                    {
                        "move_id": record.id,
                        "company_id": record.company_id.id,
                    }
                )
        return res

    def _check_verifactu_configuration(self):
        if not self.fiscal_position_id:
            raise UserError(
                _(
                    "The invoice %s cannot be sent to Verifactu because it "
                    "does not have a fiscal position."
                )
                % self.name
            )
        if not self.verifactu_tax_key:
            raise UserError(
                _(
                    "The invoice %s cannot be sent to Verifactu because it "
                    "does not have a tax key."
                )
                % self.name
            )
        if not self.verifactu_registration_key:
            raise UserError(
                _(
                    "The invoice %s cannot be sent to Verifactu because it "
                    "does not have a registration key."
                )
                % self.name
            )

        if not self._check_all_taxes_mapped():
            raise UserError(
                _(
                    "The invoice %s cannot be sent to Verifactu because it "
                    "does not have all taxes mapped."
                )
                % self.name
            )
        return super()._check_verifactu_configuration()

    def _check_all_taxes_mapped(self):
        tax_lines = self._get_aeat_tax_info()
        if not tax_lines:
            raise UserError(
                _(
                    "The invoice %s cannot be sent to Verifactu because"
                    "it does not have any taxes."
                )
                % self.name
            )
        document_date = self._get_document_fiscal_date()
        verifactu_map = verifactu_map = self._get_verifactu_map(document_date)
        tax_templates = verifactu_map.map_lines.mapped("taxes")
        mapped_taxes = self.company_id.get_taxes_from_templates(tax_templates)
        tax_lines = self._get_aeat_tax_info()
        for tax_line in tax_lines.values():
            if tax_line["tax"] not in mapped_taxes:
                return False
        return True

    def _generate_verifactu_chaining(self):
        self.ensure_one()
        self.company_id.flush_recordset(["verifactu_last_document_id"])
        try:
            with self.env.cr.savepoint():
                self.env.cr.execute(
                    "SELECT verifactu_last_document_id FROM"
                    " res_company WHERE id = %s FOR UPDATE NOWAIT",
                    [self.company_id.id],
                )
                result = self.env.cr.fetchone()[0]
                prev_doc = False
                if result:
                    document_data = result.split(",")
                    prev_doc = self.env[document_data[0]].browse(int(document_data[1]))
                self.verifactu_previous_document_id = prev_doc
                verifactu_hash_values = self._get_verifactu_hash_string()
                self.verifactu_hash_string = verifactu_hash_values
                hash_string = sha256(verifactu_hash_values.encode("utf-8"))
                self.verifactu_hash = hash_string.hexdigest().upper()
                if prev_doc:
                    prev_doc.verifactu_next_document_id = self
                doc_reference = "{model},{id}".format(model=self._name, id=self.id)
                self.env.cr.execute(
                    "UPDATE res_company SET "
                    "verifactu_last_document_id = %s"
                    "WHERE id = %s",
                    [doc_reference, self.company_id.id],
                )
                self.company_id.invalidate_recordset(["verifactu_last_document_id"])
        except psycopg2.OperationalError as err:
            if err.pgcode == "55P03":  # could not obtain the lock
                raise UserError(
                    _("Could not obtain last document sent to verifactu.")
                ) from err
            raise

    def cancel_verifactu(self):
        raise NotImplementedError

    def write(self, vals):
        for invoice in self.filtered(
            lambda x: x.is_invoice() and x.verifactu_send_state != "not_sent"
        ):
            if invoice.move_type in ["out_invoice", "out_refund"]:
                if "invoice_date" in vals:
                    self._raise_exception_verifactu(_("invoice date"))
                elif "thirdparty_number" in vals:
                    self._raise_exception_verifactu(_("third-party number"))
                elif "name" in vals:
                    self._raise_exception_verifactu(_("invoice number"))
        return super().write(vals)

    def _compute_verifactu_send_state(self):
        for rec in self:
            rec.verifactu_send_state = "not_sent"
            # Check the state from the last
            send_queue = (
                rec.verifactu_send_queue_ids
                and rec.verifactu_send_queue_ids[0]
                or False
            )
            if send_queue:
                rec.verifactu_send_state = send_queue.send_state

    def button_cancel(self):
        invoices_sent = self.filtered(
            lambda inv: inv.verifactu_enabled and inv.verifactu_send_state != "not_sent"
        )
        if invoices_sent:
            raise UserError(_("You can not cancel invoices sent to verifactu"))
        return super().button_cancel()

    def button_draft(self):
        invoices_sent = self.filtered(
            lambda inv: inv.verifactu_enabled and inv.verifactu_send_state != "not_sent"
        )
        if invoices_sent:
            raise UserError(_("You can not set to draft invoices sent to verifactu"))
        return super().button_draft()

    def _compute_verifactu_csv(self):
        for rec in self:
            rec.verifactu_csv = ""
            # Check the state from the last
            send_queue = (
                rec.verifactu_send_queue_ids
                and rec.verifactu_send_queue_ids[0]
                or False
            )
            if send_queue:
                last_response = send_queue.response_ids and send_queue.response_ids[0]
                rec.verifactu_csv = last_response.verifactu_csv

    def _search_verifactu_send_state(self, operator, value):
        queue_recs = self.env["verifactu.send.queue"].search(
            [
                ("send_state", operator, value),
                ("move_id", "!=", False),
            ]
        )
        if (operator == "=" and value) or (operator == "!=" and not value):
            new_operator = "in"
        else:
            new_operator = "not in"
        return [("id", new_operator, queue_recs.mapped("move_id").ids)]

    def resend_verifactu(self):
        for rec in self:
            rec.verifactu_send_queue_ids.write({"correction": True})
