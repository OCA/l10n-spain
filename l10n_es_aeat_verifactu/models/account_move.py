# Copyright 2024 Aures TIC - Almudena de La Puente <almudena@aurestic.es>
# Copyright 2024 Aures Tic - Jose Zambudio <jose@aurestic.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from collections import OrderedDict
from datetime import datetime
from hashlib import sha256

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
    verifactu_registration_date = fields.Datetime()

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
        "move_type",
        "fiscal_position_id",
        "fiscal_position_id.aeat_active",
    )
    def _compute_verifactu_enabled(self):
        """Compute if the invoice is enabled for the veri*FACTU"""
        for invoice in self:
            if invoice.company_id.verifactu_enabled and invoice.is_invoice():
                invoice.verifactu_enabled = (
                    invoice.fiscal_position_id
                    and invoice.fiscal_position_id.aeat_active
                ) or not invoice.fiscal_position_id
            else:
                invoice.verifactu_enabled = False

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
        return self.date

    def _get_mapping_key(self):
        """
        TODO: this method is the same in l10n_es_aeat_sii_oca, so I think that
        it should be directly in l10n_es_aeat
        """
        return self.move_type

    def _get_valid_document_states(self):
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

    def _get_verifactu_amount_tax(self):
        return self.amount_tax_signed

    def _get_verifactu_amount_total(self):
        return self.amount_total_signed

    def _get_verifactu_previous_hash(self):
        # TODO store it? search it by some kind of sequence?
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
        amountTax = round(self._get_verifactu_amount_tax(), 2)
        amountTotal = round(self._get_verifactu_amount_total(), 2)
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
                    "Destinatarios": self._get_receiver_dict(),
                }
            )

        inv_dict.update(
            {
                "Desglose": taxes_dict,
                "CuotaTotal": amount_tax,
                "ImporteTotal": amount_total,
                "Encadenamiento": self._get_chaining_invoice_dict(),
                "SistemaInformatico": self._get_verifactu_developer_dict(),
                "FechaHoraHusoGenRegistro": self._get_verifactu_registration_date(),
                "TipoHuella": "01",  # SHA-256
                "Huella": self.verifactu_hash,
            }
        )
        registroAlta.setdefault("RegistroAlta", inv_dict)
        return registroAlta

    def _get_chaining_invoice_dict(self):
        """
        TODO
        si no es el primer registro, hay que enviar el registro anterior.
        Cuando sepamos cuál es el registro anterior
        prev_invoice = self._get_previous_invoice()
        return
            {
                "RegistroAnterior" = {
                    "IDEmisorFactura": prev_invoice._get_verifactu_issuer()
                    "NumSerieFactura": prev_invoice._get_document_serial_number()
                    "FechaExpedicionFactura": prev_invoice._change_date_format(
                        prev_invoice._get_document_date())
                    "Huella": prev_invoice.verifactu_hash
                }
            }
        mientras tanto para pruebas vamos a decir siempre que es el primer registro
        """
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
        breakdown_taxes = taxes_S1 + taxes_S2 + taxes_N1 + taxes_N2
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
                # si es exenta:
                # "OperacionExenta": "", # TODO
                tax_dict.update(self._get_verifactu_tax_dict(tax_line, tax_lines))
                taxes_dict["DetalleDesglose"].append(tax_dict)
        return (
            taxes_dict,
            self._get_verifactu_amount_tax(),
            self._get_verifactu_amount_total(),
        )

    def _get_operation_type(self, tax_line, taxes_S1, taxes_S2, taxes_N1, taxes_N2):
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

    def _get_receiver_dict(self):
        self.ensure_one()
        receiver = self._aeat_get_partner()
        vat_info = receiver._parse_aeat_vat_info()
        return {
            "IDDestinatario": {
                "NombreRazon": receiver.name,
                "NIF": vat_info[2],
                # "IDOtro": {
                #     "IDType": vat_info[1],
                #     "ID": vat_info[0],
                # }
            }
        }

    def _get_verifactu_qr_values(self):
        """Get the QR values for the verifactu"""
        self.ensure_one()
        company_vat = self.company_id.partner_id._parse_aeat_vat_info()[2]
        return OrderedDict(
            [
                ("nif", company_vat),
                ("numserie", self.name),
                ("fecha", self.invoice_date.strftime("%d-%m-%Y")),
                ("importe", self.amount_total),
            ]
        )

    def _post(self, soft=True):
        verifactu_reg_date = datetime.now()
        self.write({"verifactu_registration_date": verifactu_reg_date})
        res = super()._post(soft=soft)
        for record in self:
            verifactu_hash_values = record._get_verifactu_hash_string()
            record.verifactu_hash_string = verifactu_hash_values
            hash_string = sha256(verifactu_hash_values.encode("utf-8"))
            record.verifactu_hash = hash_string.hexdigest().upper()
        return res

    def cancel_verifactu(self):
        raise NotImplementedError
