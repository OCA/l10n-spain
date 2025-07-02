# Copyright 2021 Binovo IT Human Project SL
# Copyright 2022 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64

from odoo import Command, _, api, exceptions, fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

from odoo.addons.l10n_es_ticketbai_api.models.ticketbai_invoice import (
    SiNoType,
    TicketBaiInvoiceState,
)
from odoo.addons.l10n_es_ticketbai_api.models.ticketbai_invoice_tax import (
    NotExemptedType,
)
from odoo.addons.l10n_es_ticketbai_api.ticketbai.xml_schema import TicketBaiSchema


class PosOrder(models.Model):
    _inherit = "pos.order"

    tbai_enabled = fields.Boolean(related="company_id.tbai_enabled", readonly=True)
    tbai_invoice_id = fields.Many2one(
        comodel_name="tbai.invoice", string="TicketBAI PoS Order", copy=False
    )
    tbai_invoice_ids = fields.One2many(
        comodel_name="tbai.invoice",
        inverse_name="pos_order_id",
        string="TicketBAI Invoices",
    )
    tbai_response_ids = fields.Many2many(
        comodel_name="tbai.response",
        compute="_compute_tbai_response_ids",
        string="Responses",
    )
    tbai_vat_regime_key = fields.Many2one(
        comodel_name="tbai.vat.regime.key", string="VAT Regime Key"
    )

    @api.depends("tbai_invoice_ids", "tbai_invoice_ids.state")
    def _compute_tbai_response_ids(self):
        for record in self:
            record.tbai_response_ids = [
                Command.set(record.tbai_invoice_ids.mapped("tbai_response_ids").ids)
            ]

    @api.model
    def _order_fields(self, ui_order):
        res = super()._order_fields(ui_order)
        if ui_order.get("tbai_vat_regime_key", False) and not ui_order.get(
            "to_invoice", False
        ):
            res["tbai_vat_regime_key"] = ui_order.get("tbai_vat_regime_key")
        return res

    def tbai_prepare_invoice_values(self, pos_order=None):
        self.ensure_one()
        partner = self.partner_id
        prefix = self.tbai_get_value_serie_factura()
        number = self.tbai_get_value_num_factura()
        expedition_date = self.tbai_get_value_fecha_expedicion_factura()
        expedition_hour = self.tbai_get_value_hora_expedicion_factura()
        vals = {
            "schema": TicketBaiSchema.TicketBai.value,
            "company_id": self.company_id.id,
            "simplified_invoice": SiNoType.S.value,
            "pos_order_id": self.id,
            "name": self.l10n_es_unique_id,
            "number_prefix": prefix,
            "number": number,
            "expedition_date": expedition_date,
            "expedition_hour": expedition_hour,
            "description": "/",
            "amount_total": f"{self.amount_total:.2f}",  # noqa: E231
            "vat_regime_key": self.tbai_vat_regime_key.code,
            "state": TicketBaiInvoiceState.pending.value,
        }
        if partner:
            vals["tbai_customer_ids"] = [
                Command.create(
                    {
                        "name": partner.tbai_get_value_apellidos_nombre_razon_social(),
                        "country_code": partner._parse_aeat_vat_info()[0],
                        "nif": partner.tbai_get_value_nif(),
                        "identification_number": partner.tbai_partner_identification_number
                        or partner.vat,
                        "idtype": partner.tbai_partner_idtype,
                        "address": partner.tbai_get_value_direccion(),
                        "zip": partner.zip,
                    }
                )
            ]
        if pos_order is None:
            vals["previous_tbai_invoice_id"] = self.config_id.tbai_last_invoice_id.id
        else:
            previous_order_pos_reference = pos_order.get(
                "tbai_previous_order_pos_reference", False
            )
            if previous_order_pos_reference:
                tbai_previous_order = self.search(
                    [("l10n_es_unique_id", "=", previous_order_pos_reference)], limit=1
                )
                vals[
                    "previous_tbai_invoice_id"
                ] = tbai_previous_order.tbai_invoice_id.id
            datas = base64.b64encode(pos_order["data"]["tbai_datas"].encode("utf-8"))
            vals.update(
                {
                    "datas": datas,
                    "datas_fname": "{}.xsig".format(
                        self.l10n_es_unique_id.replace("/", "-")
                    ),
                    "file_size": len(datas),
                    "signature_value": pos_order["data"]["tbai_signature_value"],
                }
            )
        gipuzkoa_tax_agency = self.env.ref(
            "l10n_es_ticketbai_api.tbai_tax_agency_gipuzkoa"
        )
        araba_tax_agency = self.env.ref("l10n_es_ticketbai_api.tbai_tax_agency_araba")
        tax_agency = self.company_id.tbai_tax_agency_id
        is_gipuzkoa_tax_agency = tax_agency == gipuzkoa_tax_agency
        is_araba_tax_agency = tax_agency == araba_tax_agency
        taxes = {}
        lines = []
        for line in self.lines:
            for tax in line.tax_ids_after_fiscal_position:
                taxes.setdefault(
                    tax.id,
                    {
                        "is_subject_to": True,
                        "is_exempted": False,
                        "not_exempted_type": NotExemptedType.S1.value,
                        "base": 0.0,
                        "amount": tax.amount,
                        "amount_total": 0.0,
                    },
                )
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                computed_tax = tax.compute_all(
                    price,
                    self.pricelist_id.currency_id,
                    line.qty,
                    product=line.product_id,
                    partner=partner,
                )
                amount_total = (
                    computed_tax["total_included"] - computed_tax["total_excluded"]
                )
                taxes[tax.id]["base"] += computed_tax["total_excluded"]
                taxes[tax.id]["amount_total"] += amount_total
            if is_gipuzkoa_tax_agency or is_araba_tax_agency:
                lines.append(
                    Command.create(
                        {
                            "description": line.name,
                            "quantity": f"{line.qty:.2f}",  # noqa: E231
                            "price_unit": f"{line.price_unit:.8f}",  # noqa: E231
                            "discount_amount": "%.2f"
                            % (line.qty * line.price_unit * line.discount / 100.0),
                            "amount_total": f"{line.price_subtotal_incl:.2f}",  # noqa: E231
                        }
                    )
                )
        vals["tbai_tax_ids"] = []
        for tax_values in taxes.values():
            tax_values["base"] = "{:.2f}".format(tax_values["base"])
            tax_values["amount"] = "{:.2f}".format(tax_values["amount"])
            tax_values["amount_total"] = "{:.2f}".format(tax_values["amount_total"])
            vals["tbai_tax_ids"].append(Command.create(tax_values))
        if is_gipuzkoa_tax_agency or is_araba_tax_agency:
            vals["tbai_invoice_line_ids"] = lines
        return vals

    def _tbai_build_invoice(self):
        TBAIInvoice = self.env["tbai.invoice"]
        for record in self:
            vals = record.tbai_prepare_invoice_values()
            tbai_invoice = TBAIInvoice.create(vals)
            tbai_invoice.build_tbai_simplified_invoice()
            record.tbai_invoice_id = tbai_invoice.id

    @api.model
    def _process_order(self, pos_order, draft, existing_order):
        if draft:
            return super()._process_order(pos_order, draft, existing_order)

        tbai_vat_regime_key = pos_order["data"].get("tbai_vat_regime_key")
        if tbai_vat_regime_key and isinstance(tbai_vat_regime_key, str):
            pos_order["data"]["tbai_vat_regime_key"] = (
                self.env["tbai.vat.regime.key"]
                .search([("code", "=", tbai_vat_regime_key)], limit=1)
                .id
            )

        order_id = super()._process_order(pos_order, draft, existing_order)
        order = self.browse(order_id)

        if order.config_id.tbai_enabled and not pos_order.get("to_invoice", False):
            vals = order.tbai_prepare_invoice_values(pos_order)
            tbai_invoice = self.env["tbai.invoice"].sudo().create(vals)
            order.tbai_invoice_id = tbai_invoice
            order.config_id.tbai_last_invoice_id = tbai_invoice

        return order.id

    def _export_for_ui(self, order):
        res = super()._export_for_ui(order)
        tbai_invoice_id = order.tbai_invoice_id
        if tbai_invoice_id:
            res["tbai_identifier"] = tbai_invoice_id.tbai_identifier
            res["tbai_qr_src"] = "data:image/png;base64," + str(
                order.tbai_invoice_id.qr.decode("UTF-8")
            )
        return res

    def _prepare_invoice_vals(self):
        res = super()._prepare_invoice_vals()
        if self.tbai_enabled:
            vat_regime_key_id = False
            if self.tbai_vat_regime_key:
                vat_regime_key_id = self.tbai_vat_regime_key.id
            elif self.fiscal_position_id:
                vat_regime_key_id = self.fiscal_position_id.tbai_vat_regime_key.id
            elif self.partner_id:
                fp = self.env["account.fiscal.position"]._get_fiscal_position(
                    self.partner_id
                )
                vat_regime_key_id = fp.tbai_vat_regime_key.id
            if not vat_regime_key_id:
                vat_regime_key_id = self.env.ref(
                    "l10n_es_ticketbai.tbai_vat_regime_01"
                ).id
            res.update({"tbai_vat_regime_key": vat_regime_key_id})
            if self.tbai_invoice_id:
                res.update(
                    {
                        "tbai_substitute_simplified_invoice": True,
                        "tbai_substitution_pos_order_id": self.id,
                    }
                )
        return res

    def tbai_get_value_serie_factura(self):
        if hasattr(self.config_id, "pos_sequence_by_device") and self.pos_device_id:
            sequence = self.pos_device_id.sequence
        else:
            sequence = self.config_id.l10n_es_simplified_invoice_sequence_id
        order_date = fields.Datetime.context_timestamp(
            self, fields.Datetime.from_string(self.date_order)
        ).strftime(DEFAULT_SERVER_DATE_FORMAT)
        prefix, suffix = sequence.with_context(
            ir_sequence_date=order_date, ir_sequence_date_range=order_date
        )._get_prefix_suffix()
        return prefix

    def tbai_get_value_num_factura(self):
        invoice_number_prefix = self.tbai_get_value_serie_factura()
        if invoice_number_prefix and not self.l10n_es_unique_id.startswith(
            invoice_number_prefix
        ):
            raise exceptions.ValidationError(
                _("Simplified Invoice Number Prefix %s is not part of Number %%!")
                % (invoice_number_prefix, self.l10n_es_unique_id)
            )
        return self.l10n_es_unique_id[len(invoice_number_prefix) :]

    def tbai_get_value_fecha_expedicion_factura(self):
        date = fields.Datetime.context_timestamp(
            self, fields.Datetime.from_string(self.date_order)
        )
        return date.strftime("%d-%m-%Y")

    def tbai_get_value_hora_expedicion_factura(self):
        date = fields.Datetime.context_timestamp(
            self, fields.Datetime.from_string(self.date_order)
        )
        return date.strftime("%H:%M:%S")
