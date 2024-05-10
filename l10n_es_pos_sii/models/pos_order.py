# Copyright 2023 Aures Tic - Almudena de la Puente <almudena@aurestic.es>
# Copyright 2023 Aures Tic - Jose Zambudio <jose@aurestic.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import UserError

SII_VALID_POS_ORDER_STATES = ["done"]


class PosOrder(models.Model):
    _name = "pos.order"
    _inherit = ["pos.order", "sii.mixin"]

    order_jobs_ids = fields.Many2many(
        comodel_name="queue.job",
        column1="pos_order_id",
        column2="job_id",
        relation="pos_order_queue_job_rel",
        string="Connector Jobs",
        copy=False,
    )

    @api.depends("company_id", "state")
    def _compute_sii_description(self):
        for order in self:
            order.sii_description = order.company_id.sii_pos_description

    @api.depends("amount_total")
    def _compute_macrodata(self):
        return super()._compute_macrodata()

    @api.depends(
        "company_id",
        "company_id.sii_enabled",
        "fiscal_position_id",
        "fiscal_position_id.aeat_active",
    )
    def _compute_sii_enabled(self):
        """Compute if the order is enabled for the SII"""
        for order in self:
            if order.company_id.sii_enabled:
                order.sii_enabled = (
                    order.fiscal_position_id and order.fiscal_position_id.aeat_active
                ) or not order.fiscal_position_id
            else:
                order.sii_enabled = False

    @api.depends("amount_total")
    def _compute_sii_refund_type(self):
        for record in self:
            if 0 > record.amount_total:
                record.sii_refund_type = "I"
            else:
                record.sii_refund_type = False

    def _export_for_ui(self, order):
        res = super()._export_for_ui(order)
        res.update(
            {
                "sii_session_closed": (
                    order.sii_enabled and order.session_id.state == "closed"
                ),
            }
        )
        return res

    def _is_sii_type_breakdown_required(self, taxes_dict):
        """As these are simplified invoices, we don't break taxes.

        El desglose se hará obligatoriamente a nivel de tipo de operación si
        cumple las 2 condiciones:
            1- No sea F2-factura simplificada o F4-asiento resumen
            2- La contraparte sea del tipo IDOtro o que sea NIF que empiece por N
        """
        return False

    def _get_sii_jobs_field_name(self):
        return "order_jobs_ids"

    def _get_valid_document_states(self):
        return SII_VALID_POS_ORDER_STATES

    def _aeat_get_partner(self):
        partner = self.session_id.config_id.default_partner_id
        if not partner:
            raise UserError(
                _("You must define a default partner for POS {}").format(
                    self.session_id.config_id.display_name,
                )
            )
        return partner

    def _is_aeat_simplified_invoice(self):
        return True

    def _get_mapping_key(self):
        return "out_invoice"

    def _get_document_date(self):
        return self.date_order

    def _get_document_fiscal_date(self):
        return self.date_order

    def _get_document_serial_number(self):
        return (self.l10n_es_unique_id or self.pos_reference)[0:60]

    def _get_document_product_exempt(self, applied_taxes):
        return set(
            self.mapped("lines")
            .filtered(
                lambda x: (
                    any(tax in x.tax_ids_after_fiscal_position for tax in applied_taxes)
                    and x.product_id.sii_exempt_cause
                    and x.product_id.sii_exempt_cause != "none"
                )
            )
            .mapped("product_id.sii_exempt_cause")
        )

    def _get_tax_info(self):
        self.ensure_one()
        taxes = {}
        for line in self.lines:
            if not line.tax_ids_after_fiscal_position:
                continue
            line_taxes = line.tax_ids_after_fiscal_position.sudo().compute_all(
                line.price_unit * (1 - (line.discount or 0.0) / 100.0),
                line.order_id.pricelist_id.currency_id or self.session_id.currency_id,
                line.qty,
                product=line.product_id,
                partner=self._aeat_get_partner(),
            )
            for line_tax in line_taxes["taxes"]:
                tax = self.env["account.tax"].browse(line_tax["id"])
                taxes.setdefault(
                    tax,
                    {"tax": tax, "amount": 0.0, "base": 0.0},
                )
                taxes[tax]["amount"] += line_tax["amount"]
                taxes[tax]["base"] += line_tax["base"]
        return taxes

    def _get_sii_tax_req(self, tax):
        """Get the associated req tax for the specified tax.

        :param self: Single invoice record.
        :param tax: Initial tax for searching for the RE linked tax.
        :return: REQ tax (or empty recordset) linked to the provided tax.
        """
        self.ensure_one()
        taxes_req = self._get_aeat_taxes_map(["RE"], self._get_document_fiscal_date())
        re_lines = self.lines.filtered(
            lambda x: tax in x.tax_ids_after_fiscal_position
            and x.tax_ids_after_fiscal_position & taxes_req
        )
        req_tax = re_lines.mapped("tax_ids_after_fiscal_position") & taxes_req
        if len(req_tax) > 1:
            raise UserError(_("There's a mismatch in taxes for RE. Check them."))
        return req_tax

    def _get_document_amount_total(self):
        return self.amount_total

    def _get_sii_invoice_type(self):
        return "R5" if self.amount_total < 0.0 else "F2"

    def _get_aeat_invoice_dict_out(self, cancel=False):
        inv_dict = super()._get_aeat_invoice_dict_out(cancel=cancel)
        if self.amount_total < 0.0:
            inv_dict["FacturaExpedida"]["TipoRectificativa"] = "I"
        return inv_dict
