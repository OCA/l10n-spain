# Copyright 2024 Aures TIC - Almudena de La Puente
# Copyright 2024 Aures Tic - Jose Zambudio
# Copyright 2025 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from collections import OrderedDict
from datetime import datetime

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import UserError

VERIFACTU_VALID_INVOICE_STATES = ["posted"]


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "verifactu.mixin"]

    verifactu_refund_specific_type = fields.Selection(
        string="VERI*FACTU refund specific type",
        selection=[
            ("R1", "Art. 80.1 y 80.2 y error fundado en derecho"),
            ("R2", "Art. 80.3"),
            ("R3", "Art. 80.4"),
            ("R4", "Resto"),
            ("R5", "De factura simplificada"),
        ],
        help="Fill this field when the refund are one of the specific cases"
        " of article 80 of LIVA for notifying to VERI*FACTU with the proper"
        " invoice type.",
    )

    @api.depends("move_type")
    def _compute_verifactu_refund_type(self):
        refunds = self.filtered(lambda x: x.move_type == "out_refund")
        refunds.verifactu_refund_type = "I"
        (self - refunds).verifactu_refund_type = False

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
        """Compute if the invoice is enabled for the VERI*FACTU"""
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
                    invoice.fiscal_position_id.aeat_active
                    if invoice.fiscal_position_id
                    else True
                )
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
                    ("verifactu_tax_key", "=", "01"),
                ]
                verifactu_key_obj = self.env["verifactu.registration.key"]
                document.verifactu_registration_key = verifactu_key_obj.search(
                    domain, limit=1
                )

    def _get_verifactu_document_type(self):
        invoice_type = ""
        if self.move_type in ["out_invoice", "out_refund"]:
            is_simplified = self._is_aeat_simplified_invoice()
            invoice_type = "F2" if is_simplified else "F1"
            if self.move_type == "out_refund":
                if self.verifactu_refund_specific_type:
                    invoice_type = self.verifactu_refund_specific_type
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
        if self.last_verifactu_invoice_entry_id:
            return self.last_verifactu_invoice_entry_id.previous_hash or ""
        return ""

    def _get_verifactu_registration_date(self):
        # Date format must be ISO 8601
        return (
            pytz.utc.localize(self.verifactu_registration_date)
            .astimezone()
            .isoformat(timespec="seconds")
        )

    def _get_verifactu_hash_string(self):
        """Gets the VERI*FACTU hash string"""
        if (
            not self.verifactu_enabled
            or self.state == "draft"
            or self.move_type not in ("out_invoice", "out_refund")
        ):
            return ""
        issuer = self._get_verifactu_issuer()
        serial_number = self._get_document_serial_number()
        expedition_date = self._get_verifactu_date(self._get_document_date())
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

    def _get_verifactu_chaining(self):
        return self.company_id.verifactu_chaining_id

    def _get_verifactu_invoice_dict_out(self, cancel=False):
        """Build dict with data to send to AEAT WS for document types:
        out_invoice and out_refund.

        :param cancel: It indicates if the dictionary is for sending a
          cancellation of the document.
        :return: documents (dict) : Dict XML with data for this document.
        """
        self.ensure_one()
        document_date = self._get_verifactu_date(self._get_document_date())
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
                    orig_document_date = self._get_verifactu_date(
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
        inv_dict["DescripcionOperacion"] = self._get_verifactu_description()
        if verifactu_doc_type not in ("F2", "R5"):
            inv_dict["Destinatarios"] = self._get_verifactu_receiver_dict()
        elif verifactu_doc_type in ("F2", "R5"):
            inv_dict["FacturaSinIdentifDestinatarioArt61d"] = "S"
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
        if self.aeat_state in ("sent_w_errors", "incorrect"):
            # en caso de subsanación, debe generar un nuevo hash en la factura
            inv_dict["Subsanacion"] = "S"
        if self.aeat_state == "incorrect":
            inv_dict["RechazoPrevio"] = "X"
        registroAlta.setdefault("RegistroAlta", inv_dict)
        return registroAlta

    def _get_verifactu_chaining_invoice_dict(self):
        if self.last_verifactu_invoice_entry_id:
            prev_entry = self.last_verifactu_invoice_entry_id.previous_invoice_entry_id
            if prev_entry:
                doc = prev_entry.document
                return {
                    "RegistroAnterior": {
                        "IDEmisorFactura": doc._get_verifactu_issuer(),
                        "NumSerieFactura": doc._get_document_serial_number(),
                        "FechaExpedicionFactura": doc._get_verifactu_date(
                            doc._get_document_date()
                        ),
                        "Huella": prev_entry.document_hash,
                    }
                }
        return {"PrimerRegistro": "S"}

    def _get_verifactu_tax_dict(self, tax_line, tax_lines):
        """Get the VERI*FACTU tax dictionary for the passed tax line.

        :param self: Single invoice record.
        :param tax_line: Tax line that is being analyzed.
        :param tax_lines: Dictionary of processed invoice taxes for further operations
            (like REQ).
        :return: A dictionary with the corresponding VERI*FACTU tax values.
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
        """Get the VERI*FACTU tax dictionary for the passed tax line.

        :param self: Single invoice record.
        :param tax_line: Tax line that is being analyzed.
        :return: A dictionary with the corresponding VERI*FACTU tax values.
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
        document_date = self._get_document_date()
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
        document_date = self._get_document_date()
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
                if operation_type not in ("N1", "N2"):
                    new_tax_dict = self._get_verifactu_tax_dict(tax_line, tax_lines)
                    tax_dict.update(new_tax_dict)
                else:
                    tax_dict.update(self._get_verifactu_tax_dict_ns(tax_line))
                taxes_dict["DetalleDesglose"].append(tax_dict)
            elif tax in excluded_taxes:
                not_in_taxes += tax_line["amount"]
            elif tax not in taxes_RE:
                raise UserError(_("%s tax is not mapped to VERI*FACTU.", tax.name))
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
        country_code, identifier_type, identifier = receiver._parse_aeat_vat_info()
        if identifier:
            identifier = "".join(e for e in identifier if e.isalnum()).upper()
        else:
            identifier = "NO_DISPONIBLE"
            identifier_type = "06"
        if identifier_type == "":
            return {"IDDestinatario": {"NombreRazon": receiver.name, "NIF": identifier}}
        if (
            receiver._map_aeat_country_code(country_code)
            in receiver._get_aeat_europe_codes()
        ):
            identifier = country_code + identifier
        return {
            "IDDestinatario": {
                "NombreRazon": receiver.name,
                "IDOtro": {
                    "CodigoPais": receiver.country_id.code,
                    "IDType": identifier_type,
                    "ID": identifier,
                },
            }
        }

    def _get_verifactu_qr_values(self):
        """Get the QR values for the VERI*FACTU"""
        self.ensure_one()
        company_vat = self.company_id.partner_id._parse_aeat_vat_info()[2]
        _taxes_dict, _amount_tax, amount_total = self._get_verifactu_taxes_and_total()
        return OrderedDict(
            [
                ("nif", company_vat),
                ("numserie", self.name),
                ("fecha", self.invoice_date.strftime("%d-%m-%Y")),
                ("importe", f"{amount_total:.2f}"),  # noqa
            ]
        )

    def _post(self, soft=True):
        res = super()._post(soft=soft)
        for record in self.sorted(lambda inv: inv.name):
            if record.verifactu_enabled and record.aeat_state == "not_sent":
                record._check_verifactu_configuration()
                record.verifactu_registration_date = datetime.now()
                record._generate_verifactu_chaining()
        return res

    def _check_verifactu_configuration(self, suffixes=None):
        if not suffixes:
            suffixes = []
        # Too restrictive limitation
        # if not self.fiscal_position_id:
        #     suffixes.append(_("- It does not have a fiscal position."))
        if not self.verifactu_tax_key:
            suffixes.append(_("- It does not have a tax key."))
        if not self.verifactu_registration_key:
            suffixes.append(_("- It does not have a registration key."))
        if not self._check_inconsistent_taxes():
            suffixes.append(_("- There are some inconsistent taxes on lines."))
        if not self._check_all_taxes_mapped():
            suffixes.append(_("- It does not have all taxes mapped."))
        return super()._check_verifactu_configuration(suffixes=suffixes)

    def _check_inconsistent_taxes(self):
        document_date = self._get_document_date()
        taxes_S1 = self._get_verifactu_taxes_map(["S1"], document_date)
        taxes_S2 = self._get_verifactu_taxes_map(["S2"], document_date)
        taxes_RE = self._get_verifactu_taxes_map(["RE"], document_date)
        for line in self.invoice_line_ids:
            taxes_in_s1 = line.tax_ids.filtered(lambda x: x in taxes_S1)
            if len(taxes_in_s1) > 1:
                return False
            taxes_in_s2 = line.tax_ids.filtered(lambda x: x in taxes_S2)
            if len(taxes_in_s2) > 1:
                return False
            taxes_in_RE = line.tax_ids.filtered(lambda x: x in taxes_RE)
            if len(taxes_in_RE) > 1:
                return False
        return True

    def _check_all_taxes_mapped(self):
        if not (tax_lines := self._get_aeat_tax_info()):
            return False
        verifactu_map = self._get_verifactu_map(self._get_document_date())
        tax_templates = verifactu_map.map_lines.tax_xmlid_ids
        mapped_taxes = self.env["account.tax"]
        for template in tax_templates:
            tax_id = self.company_id._get_tax_id_from_xmlid(template.name)
            mapped_taxes |= self.env["account.tax"].browse(tax_id)
        for tax_line in tax_lines.values():
            if tax_line["tax"] not in mapped_taxes:
                return False
        return True

    def cancel_verifactu(self):
        raise NotImplementedError

    def write(self, vals):
        for invoice in self.filtered(
            lambda x: x.is_invoice() and x.aeat_state != "not_sent"
        ):
            if invoice.move_type in ["out_invoice", "out_refund"]:
                if "invoice_date" in vals:
                    self._raise_exception_verifactu(_("invoice date"))
                elif "thirdparty_number" in vals:
                    self._raise_exception_verifactu(_("third-party number"))
                elif "name" in vals:
                    self._raise_exception_verifactu(_("invoice number"))
        return super().write(vals)

    def button_cancel(self):
        invoices_sent = self.filtered(
            lambda inv: inv.verifactu_enabled and inv.aeat_state != "not_sent"
        )
        if invoices_sent:
            raise UserError(_("You can not cancel invoices sent to VERI*FACTU."))
        return super().button_cancel()

    def button_draft(self):
        invoices_sent = self.filtered(
            lambda inv: inv.verifactu_enabled and inv.aeat_state != "not_sent"
        )
        if invoices_sent:
            raise UserError(_("You can not set to draft invoices sent to VERI*FACTU."))
        return super().button_draft()

    def resend_verifactu(self):
        for rec in self:
            if (
                rec.aeat_state in ("sent_w_errors", "incorrect")
                and rec.last_verifactu_invoice_entry_id
                and not rec.last_verifactu_invoice_entry_id.send_state == "not_sent"
            ):
                entry_type = (
                    "modify" if rec.aeat_state == "sent_w_errors" else "register"
                )
                rec.verifactu_registration_date = datetime.now()
                rec._generate_verifactu_chaining(entry_type=entry_type)
