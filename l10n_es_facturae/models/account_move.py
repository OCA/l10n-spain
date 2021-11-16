# Copyright 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64
from collections import defaultdict

from lxml import etree

from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError

from odoo.addons.base.models.ir_ui_view import (
    transfer_modifiers_to_node,
    transfer_node_to_modifiers,
)


class AccountMove(models.Model):
    _inherit = "account.move"

    facturae = fields.Boolean(compute="_compute_facturae")
    correction_method = fields.Selection(
        selection=[
            ("01", "Rectificación íntegra"),
            ("02", "Rectificación por diferencias"),
            (
                "03",
                "Rectificación por descuento por volumen de operaciones "
                "durante un periodo",
            ),
            ("04", "Autorizadas por la Agencia Tributaria"),
        ]
    )

    facturae_refund_reason = fields.Selection(
        selection=[
            ("01", "Número de la factura"),
            ("02", "Serie de la factura"),
            ("03", "Fecha expedición"),
            ("04", "Nombre y apellidos/Razón social - Emisor"),
            ("05", "Nombre y apellidos/Razón social - Receptor"),
            ("06", "Identificación fiscal Emisor/Obligado"),
            ("07", "Identificación fiscal Receptor"),
            ("08", "Domicilio Emisor/Obligado"),
            ("09", "Domicilio Receptor"),
            ("10", "Detalle Operación"),
            ("11", "Porcentaje impositivo a aplicar"),
            ("12", "Cuota tributaria a aplicar"),
            ("13", "Fecha/Periodo a aplicar"),
            ("14", "Clase de factura"),
            ("15", "Literales legales"),
            ("16", "Base imponible"),
            ("80", "Cálculo de cuotas repercutidas"),
            ("81", "Cálculo de cuotas retenidas"),
            ("82", "Base imponible modificada por devolución de envases" "/embalajes"),
            ("83", "Base imponible modificada por descuentos y " "bonificaciones"),
            (
                "84",
                "Base imponible modificada por resolución firme, judicial "
                "o administrativa",
            ),
            (
                "85",
                "Base imponible modificada cuotas repercutidas no "
                "satisfechas. Auto de declaración de concurso",
            ),
        ]
    )
    facturae_start_date = fields.Date(
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    facturae_end_date = fields.Date(
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    l10n_es_facturae_status = fields.Selection(
        [], tracking=True, readonly=True, string="Facturae status", copy=False
    )
    l10n_es_facturae_cancellation_status = fields.Selection(
        [],
        tracking=True,
        readonly=True,
        string="Facturae cancellation status",
        copy=False,
    )
    l10n_es_facturae_attachment_ids = fields.One2many(
        "l10n.es.facturae.attachment",
        inverse_name="move_id",
        copy=False,
    )
    thirdparty_invoice = fields.Boolean(
        string="Third-party invoice",
        copy=False,
        compute="_compute_thirdparty_invoice",
        store=True,
        readonly=False,
    )
    thirdparty_number = fields.Char(
        string="Third-party number",
        index=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=False,
        help="Número de la factura emitida por un tercero.",
    )

    @api.depends("journal_id")
    def _compute_thirdparty_invoice(self):
        for item in self:
            item.thirdparty_invoice = item.journal_id.thirdparty_invoice

    def _get_edi_missing_records(self):
        result = super()._get_edi_missing_records()
        if result:
            return result
        if self.move_type not in ["out_invoice", "out_refund"]:
            return False
        partner = self.partner_id
        if not partner.facturae or not partner.l10n_es_facturae_sending_code:
            return False
        exchange_type = self._get_exchange_type_map()[
            partner.l10n_es_facturae_sending_code
        ]
        if not exchange_type:
            return False
        return not self._has_exchange_record(
            exchange_type, self.env.ref("l10n_es_facturae.backend_facturae")
        )

    @api.model
    def _edi_missing_records_fields(self):
        result = super()._edi_missing_records_fields()
        return result + [
            "l10n_es_facturae_status",
            "partner_id.l10n_es_facturae_sending_code",
        ]

    @api.constrains("facturae_start_date", "facturae_end_date")
    def _check_facturae_date(self):
        for record in self:
            if bool(record.facturae_start_date) != bool(record.facturae_end_date):
                raise ValidationError(
                    _(
                        "FacturaE start and end dates are both required if one of "
                        "them is filled"
                    )
                )
            if (
                record.facturae_start_date
                and record.facturae_start_date > record.facturae_end_date
            ):
                raise ValidationError(_("Start date cannot be later than end date"))

    @api.depends("partner_id.facturae", "move_type")
    def _compute_facturae(self):
        for record in self:
            record.facturae = record.partner_id.facturae and record.move_type in [
                "out_invoice",
                "out_refund",
            ]

    def get_exchange_rate(self, euro_rate, currency_rate):
        if not euro_rate and not currency_rate:
            return fields.Datetime.now().strftime("%Y-%m-%d")
        if not currency_rate:
            return fields.Datetime.to_datetime(euro_rate.name).strftime("%Y-%m-%d")
        if not euro_rate:
            return fields.Datetime.to_datetime(currency_rate.name).strftime("%Y-%m-%d")
        currency_date = fields.Datetime.to_datetime(currency_rate.name)
        euro_date = fields.Datetime.to_datetime(currency_rate.name)
        if currency_date < euro_date:
            return currency_date.strftime("%Y-%m-%d")
        return euro_date.strftime("%Y-%m-%d")

    def get_refund_reason_string(self):
        return dict(
            self.fields_get(allfields=["facturae_refund_reason"])[
                "facturae_refund_reason"
            ]["selection"]
        )[self.facturae_refund_reason]

    def get_correction_method_string(self):
        return dict(
            self.fields_get(allfields=["correction_method"])["correction_method"][
                "selection"
            ]
        )[self.correction_method]

    def _get_valid_move_statuses(self):
        return ["posted"]

    def validate_facturae_fields(self):
        lines = self.line_ids.filtered(
            lambda r: not r.display_type and not r.exclude_from_invoice_tab
        )
        for line in lines:
            if not line.tax_ids:
                raise ValidationError(
                    _("Taxes not provided in move line " "%s") % line.name
                )
        if not self.partner_id.vat:
            raise ValidationError(_("Partner vat not provided"))
        if not self.company_id.partner_id.vat:
            raise ValidationError(_("Company vat not provided"))
        if len(self.partner_id.vat) < 3:
            raise ValidationError(_("Partner vat is too small"))
        if not self.partner_id.state_id:
            raise ValidationError(_("Partner state not provided"))
        if len(self.company_id.vat) < 3:
            raise ValidationError(_("Company vat is too small"))
        if not self.payment_mode_id:
            raise ValidationError(_("Payment mode is required"))
        if self.payment_mode_id.facturae_code:
            partner_bank = self.partner_banks_to_show()[:1]
            if not partner_bank:
                raise ValidationError(_("Partner bank is missing"))
            if partner_bank.bank_id.bic and len(partner_bank.bank_id.bic) != 11:
                raise ValidationError(_("Selected account BIC must be 11"))
            if len(partner_bank.acc_number) < 5:
                raise ValidationError(_("Selected account is too small"))
        if self.state not in self._get_valid_move_statuses():
            raise ValidationError(
                _(
                    "You can only create Factura-E files for "
                    "moves that have been validated."
                )
            )
        return

    def _get_facturae_move_attachments(self):
        result = []
        if self.partner_id.attach_invoice_as_annex:
            action = self.env.ref("account.account_invoices")
            content, content_type = action._render(self.ids)
            result.append(
                {
                    "data": base64.b64encode(content),
                    "content_type": content_type,
                    "encoding": "BASE64",
                    "description": _("Invoice %s") % self.name,
                    "compression": False,
                }
            )
        for attachment in self.l10n_es_facturae_attachment_ids:
            description, content_type = attachment.filename.rsplit(".", 1)
            result.append(
                {
                    "data": attachment.file,
                    "content_type": content_type,
                    "encoding": "BASE64",
                    "description": description,
                    "compression": False,
                }
            )
        return result

    def get_facturae_version(self):
        return (
            self.partner_id.facturae_version
            or self.company_id.facturae_version
            or "3_2"
        )

    def _has_exchange_record_domain(
        self, exchange_type, backend=False, extra_domain=False
    ):
        domain = super()._has_exchange_record_domain(
            exchange_type, backend=backend, extra_domain=extra_domain
        )
        if exchange_type == "l10n_es_facturae":
            domain += [
                "|",
                ("l10n_es_facturae_status", "=", False),
                (
                    "l10n_es_facturae_status",
                    "not in",
                    self._get_l10n_es_facturae_excluded_status(),
                ),
            ]
        return domain

    @api.model
    def _get_l10n_es_facturae_excluded_status(self):
        return []

    def _get_l10n_es_facturae_backend(self):
        """To be inherited by all facturae sending modules"""
        return False

    def _get_facturae_tax_info(self):
        self.ensure_one()
        output_taxes = defaultdict(lambda: {"base": 0, "amount": 0})
        withheld_taxes = defaultdict(lambda: {"base": 0, "amount": 0})
        for line in self.line_ids:
            sign = -1 if self.move_type[:3] == "out" else 1
            for tax in line.tax_ids:
                if tools.float_compare(tax.amount, 0, precision_digits=2) >= 0:
                    output_taxes[tax]["base"] += line.balance * sign
                else:
                    withheld_taxes[tax]["base"] += line.balance * sign
        for tax in output_taxes:
            output_taxes[tax]["amount"] = output_taxes[tax]["base"] * tax.amount / 100
        for tax in withheld_taxes:
            withheld_taxes[tax]["amount"] = (
                withheld_taxes[tax]["base"] * tax.amount / 100
            )
        return output_taxes, withheld_taxes

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        """Thirdparty fields are added to the form view only if they don't exist
        previously (l10n_es_aeat_sii_oca addon also has the same field names).
        """
        res = super().fields_view_get(
            view_id=view_id,
            view_type=view_type,
            toolbar=toolbar,
            submenu=submenu,
        )
        if view_type == "form":
            doc = etree.XML(res["arch"])
            node = doc.xpath("//field[@name='thirdparty_invoice']")
            if node:
                return res
            for node in doc.xpath("//field[@name='ref']"):
                attrs = {
                    "required": [("thirdparty_invoice", "=", True)],
                    "invisible": [("thirdparty_invoice", "=", False)],
                }
                elem = etree.Element(
                    "field",
                    {"name": "thirdparty_number", "attrs": str(attrs)},
                )
                modifiers = {}
                transfer_node_to_modifiers(elem, modifiers)
                transfer_modifiers_to_node(modifiers, elem)
                node.addnext(elem)
                res["fields"].update(self.fields_get(["thirdparty_number"]))
                elem = etree.Element("field", {"name": "thirdparty_invoice"})
                node.addnext(elem)
                res["fields"].update(self.fields_get(["thirdparty_invoice"]))
            res["arch"] = etree.tostring(doc)
        return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    facturae_receiver_contract_reference = fields.Char()
    facturae_receiver_contract_date = fields.Date()
    facturae_receiver_transaction_reference = fields.Char()
    facturae_receiver_transaction_date = fields.Date()
    facturae_issuer_contract_reference = fields.Char()
    facturae_issuer_contract_date = fields.Date()
    facturae_issuer_transaction_reference = fields.Char()
    facturae_issuer_transaction_date = fields.Date()
    facturae_file_reference = fields.Char()
    facturae_file_date = fields.Date()
    facturae_start_date = fields.Date()
    facturae_end_date = fields.Date()
    facturae_transaction_date = fields.Date()

    @api.constrains("facturae_start_date", "facturae_end_date")
    def _check_facturae_date(self):
        for record in self:
            if bool(record.facturae_start_date) != bool(record.facturae_end_date):
                raise ValidationError(
                    _(
                        "FacturaE start and end dates are both required if one of "
                        "them is filled"
                    )
                )
            if (
                record.facturae_start_date
                and record.facturae_start_date > record.facturae_end_date
            ):
                raise ValidationError(_("Start date cannot be later than end date"))

    def button_edit_facturae_fields(self):
        self.ensure_one()
        view = self.env.ref("l10n_es_facturae.view_facturae_fields")
        return {
            "name": _("Facturae Configuration"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": self._name,
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "new",
            "res_id": self.id,
            "context": self.env.context,
        }


class L10nEsFacturaeAttachment(models.Model):
    _name = "l10n.es.facturae.attachment"
    _description = "Facturae Attachment"

    move_id = fields.Many2one("account.move", required=True, ondelete="cascade")
    file = fields.Binary(required=True)
    filename = fields.Char()
