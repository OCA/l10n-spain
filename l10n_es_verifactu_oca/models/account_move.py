# Copyright 2024 Aures TIC - Almudena de La Puente
# Copyright 2024 Aures Tic - Jose Zambudio
# Copyright 2025 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from collections import OrderedDict
from datetime import datetime

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

VERIFACTU_VALID_INVOICE_STATES = ["posted"]
VERIFACTU_OPERATION_MAPPING = {
    "sujeto": "S1",
    "sujeto_agricultura": "S1",
    "sujeto_isp": "S2",
    "no_sujeto": "N1",
    "no_sujeto_loc": "N2",
    "no_deducible": "S1",
    # Not included here: exento, retencion, recargo, dua & ignore
}


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
    verifactu_substituted_invoice_ids = fields.Many2many(
        string="VERI*FACTU substituted simplified invoices",
        comodel_name="account.move",
        relation="account_move_verifactu_substituted_rel",
        column1="move_id",
        column2="substituted_move_id",
        copy=False,
        domain="[('move_type', '=', 'out_invoice'), ('state', '=', 'posted')]",
        help="Simplified invoices that this invoice substitutes. Filling it "
        "makes the invoice be registered at VERI*FACTU as F3, quoting them in "
        "the FacturasSustituidas block. The substituted invoices are left as "
        "they are: a substitution is not a rectification, so they must be "
        "neither cancelled nor rectified, and their amounts are not declared "
        "again.",
    )

    @api.constrains("verifactu_substituted_invoice_ids")
    def _check_verifactu_substituted_invoice_ids(self):
        """A simplified invoice can only be exchanged for one ordinary invoice.

        Substituting it twice would declare the same operation as two different
        F3, which is precisely what the substitution mechanism avoids.
        """
        for move in self.filtered("verifactu_substituted_invoice_ids"):
            substituted = move.verifactu_substituted_invoice_ids
            if move in substituted:
                raise ValidationError(
                    _("An invoice cannot substitute itself: %s", move.display_name)
                )
            duplicated = self.search(
                [
                    ("id", "!=", move.id),
                    ("state", "!=", "cancel"),
                    ("verifactu_substituted_invoice_ids", "in", substituted.ids),
                ],
                limit=1,
            )
            if duplicated:
                raise ValidationError(
                    _(
                        "Some of the simplified invoices substituted by %(move)s "
                        "are already substituted by %(duplicated)s. A simplified "
                        "invoice can only be exchanged for one ordinary invoice.",
                        move=move.display_name,
                        duplicated=duplicated.display_name,
                    )
                )

    def _get_verifactu_substituted_documents(self):
        documents = super()._get_verifactu_substituted_documents()
        return documents + list(self.verifactu_substituted_invoice_ids)

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
            elif self._get_verifactu_substituted_documents():
                # Ordinary invoice issued in substitution of simplified
                # invoices already registered and declared. It is not a
                # rectification: the substituted ones stay as they are.
                invoice_type = "F3"
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
        # Don't use third party number for now, until
        # the full third party invoice management is implemented.
        # if self.thirdparty_invoice:
        #     serial_number = self.thirdparty_number[0:60]
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

    def _get_verifactu_hash_string(self, cancel=False):
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
        if not cancel:
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
        else:
            verifactu_hash_string = (
                f"IDEmisorFacturaAnulada={issuer}&"
                f"NumSerieFacturaAnulada={serial_number}&"
                f"FechaExpedicionFacturaAnulada={expedition_date}&"
                f"Huella={previous_hash}&"
                f"FechaHoraHusoGenRegistro={registration_date}"
            )
        return verifactu_hash_string

    def _get_verifactu_chaining(self):
        return self.company_id.verifactu_chaining_id

    def _get_verifactu_invoice_dict_out(self):
        """Build dict with data to send to AEAT WS for document types:
        out_invoice and out_refund.
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
        if verifactu_doc_type == "F3":
            inv_dict["FacturasSustituidas"] = {
                "IDFacturaSustituida": [
                    substituted["IDFacturaSustituida"]
                    for substituted in self._get_verifactu_substituted_invoices_dict()
                ]
            }
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

    def _get_verifactu_cancel_invoice_dict_out(self):
        """Build cancel dict with data to send to AEAT WS for document types:
        out_invoice and out_refund.
        :return: documents (dict) : Dict XML with data for this document.
        """
        self.ensure_one()
        document_date = self._get_verifactu_date(self._get_document_date())
        company = self.company_id
        serial_number = self._get_document_serial_number()
        company_vat = company.partner_id._parse_aeat_vat_info()[2]
        registroAnulacion = {}
        inv_dict = {
            "IDVersion": self._get_verifactu_version(),
            "IDFactura": {
                "IDEmisorFacturaAnulada": company_vat,
                "NumSerieFacturaAnulada": serial_number,
                "FechaExpedicionFacturaAnulada": document_date,
            },
        }
        if self.aeat_state == "cancel_incorrect":
            inv_dict["RechazoPrevio"] = "S"
        inv_dict.update(
            {
                "Encadenamiento": self._get_verifactu_chaining_invoice_dict(),
                "SistemaInformatico": self._get_verifactu_developer_dict(),
                "FechaHoraHusoGenRegistro": self._get_verifactu_registration_date(),
                "TipoHuella": "01",  # SHA-256
                "Huella": self.verifactu_hash,
            }
        )
        registroAnulacion.setdefault("RegistroAnulacion", inv_dict)
        return registroAnulacion

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
        tax_dict = {"BaseImponibleOimporteNoSujeto": tax_base_amount}
        operation_type = VERIFACTU_OPERATION_MAPPING.get(tax.l10n_es_type)
        if tax.l10n_es_type == "exento":
            tax_dict["OperacionExenta"] = tax.l10n_es_exempt_reason
            return tax_dict
        tax_dict["CalificacionOperacion"] = operation_type
        if operation_type in ("N1", "N2"):
            return tax_dict
        if tax.amount_type == "group":
            tax_percentage = abs(tax.children_tax_ids.filtered("amount")[:1].amount)
        else:
            tax_percentage = abs(tax.amount)
        tax_dict["TipoImpositivo"] = str(tax_percentage)
        tax_dict["CuotaRepercutida"] = tax_line["amount"]
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
        for tax, tax_line in tax_lines.items():
            if tax in taxes_not_in_total:
                not_in_amount_total += tax_line["amount"]
            elif tax in base_not_in_total:
                not_in_amount_total += tax_line["base"]
            if tax in breakdown_taxes:
                tax_dict = {
                    "Impuesto": self.verifactu_tax_key,
                    "ClaveRegimen": self.verifactu_registration_key_code,
                }
                tax_dict.update(self._get_verifactu_tax_dict(tax_line, tax_lines))
                taxes_dict["DetalleDesglose"].append(tax_dict)
            elif tax in excluded_taxes:
                not_in_taxes += tax_line["amount"]
            elif tax not in taxes_RE:
                raise UserError(_("%s tax is not mapped to VERI*FACTU.", tax.name))
        amount_tax = self.amount_tax_signed - not_in_taxes
        amount_total = self.amount_total_signed - not_in_amount_total
        return (taxes_dict, amount_tax, amount_total)

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
        for record in self.sorted(lambda inv: inv.name or ""):
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
        suffixes += self._check_verifactu_substituted_documents()
        return super()._check_verifactu_configuration(suffixes=suffixes)

    def _check_verifactu_substituted_documents(self):
        """Checks that only apply to an invoice substituting simplified ones (F3)."""
        suffixes = []
        if self._get_verifactu_document_type() != "F3":
            return suffixes
        # An F3 always carries the destinatario, and a counter customer is
        # often created without a VAT number or without a country.
        partner = self._aeat_get_partner()
        if not partner or not partner._is_valid_verifactu_receiver():
            suffixes.append(
                _(
                    "- It substitutes simplified invoices, so it is registered "
                    "as F3, which must always identify the customer. Set the "
                    "customer's VAT number, and also their country when that "
                    "number is not Spanish."
                )
            )
        for document in self._get_verifactu_substituted_documents():
            if not document.last_verifactu_invoice_entry_id:
                suffixes.append(
                    _(
                        "- It substitutes %s, which was never registered at "
                        "VERI*FACTU. Only an already registered and declared "
                        "simplified invoice can be substituted.",
                        document.display_name,
                    )
                )
            elif document._get_verifactu_document_type() not in ("F2", "R5"):
                suffixes.append(
                    _(
                        "- It substitutes %s, which is not a simplified "
                        "invoice. Only simplified invoices can be substituted.",
                        document.display_name,
                    )
                )
        return suffixes

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
        tax_xml_ids = verifactu_map.map_lines.tax_xmlid_ids.mapped("name")
        mapped_taxes = self.company_id._get_taxes_from_xmlids(tax_xml_ids)
        for tax_line in tax_lines.values():
            if tax_line["tax"] not in mapped_taxes:
                return False
        return True

    def cancel_verifactu(self):
        self.ensure_one()
        if (
            self.aeat_state
            in (
                "sent_w_errors",
                "sent",
                "cancel_incorrect",
                "cancel_w_errors",
            )
            and self.last_verifactu_invoice_entry_id
            and not self.last_verifactu_invoice_entry_id.send_state == "not_sent"
        ):
            if self.state != "cancel":
                action = self.env["ir.actions.act_window"]._for_xml_id(
                    "l10n_es_verifactu_oca.verifactu_cancel_invoice_wizard_action"
                )
                action["context"] = {
                    "default_invoice_id": self.id,
                }
                return action
            entry_type = "cancel"
            self.verifactu_registration_date = datetime.now()
            self._generate_verifactu_chaining(entry_type=entry_type)

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
                elif "verifactu_substituted_invoice_ids" in vals:
                    self._raise_exception_verifactu(_("substituted simplified invoices"))
        return super().write(vals)

    def button_cancel(self):
        invoices_sent = self.filtered(
            lambda inv: inv.verifactu_enabled and inv.aeat_state != "not_sent"
        )
        if invoices_sent and not self.env.context.get("verifactu_cancel"):
            raise UserError(_("You can not cancel invoices sent to VERI*FACTU."))
        return super().button_cancel()

    def _check_draftable(self):
        # Don't block the intermediate pass to draft when cancelling VERI*FACTU invoice
        if not self.env.context.get("verifactu_cancel"):
            return super()._check_draftable()

    def button_draft(self):
        # Don't allow go to draft, except when cancelling VERI*FACTU invoice via wizard
        invoices_sent = self.filtered(
            lambda inv: inv.verifactu_enabled and inv.aeat_state != "not_sent"
        )
        if invoices_sent and not self.env.context.get("verifactu_cancel"):
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
