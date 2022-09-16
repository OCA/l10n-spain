# Copyright 2021 Binovo IT Human Project SL
# Copyright 2022 Landoo Sistemas de Informacion SL
# Copyright 2022 Advanced Programming Solutions SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    tbai_substitution_pos_order_id = fields.Many2one(
        comodel_name="pos.order",
        copy=False,
        help="Link between a validated Customer Invoice and its substitute.",
    )

    def tbai_prepare_invoice_values(self):
        res = super().tbai_prepare_invoice_values()
        if not res.get("vat_regime_key", False):
            res["vat_regime_key"] = (
                self.env["tbai.vat.regime.key"]
                .search([("code", "=", "01")], limit=1)
                .code
            )
        if self.tbai_substitute_simplified_invoice:
            refunded_pos_order = self.tbai_substitution_pos_order_id
            res.update(
                {
                    "is_invoice_refund": False,
                    "tbai_invoice_refund_ids": [
                        (
                            0,
                            0,
                            {
                                "number_prefix": (
                                    refunded_pos_order.tbai_get_value_serie_factura()
                                ),
                                "number": (
                                    refunded_pos_order.tbai_get_value_num_factura()
                                ),
                                "expedition_date": (
                                    refunded_pos_order.tbai_get_value_fecha_expedicion_factura()
                                ),
                            },
                        )
                    ],
                }
            )
        return res

    # For Ticketbai is mandatory to specify origin invoice in refunds
    def _post(self, soft=True):
        def set_reverse_entries(self):
            for invoice in self:
                pos_order_ids = invoice.sudo().pos_order_ids
                for pos_order in pos_order_ids:
                    pos_refunded_orders = pos_order.refunded_order_ids
                    for refunded_order_id in pos_refunded_orders:
                        refunded_invoice_id = refunded_order_id.account_move
                        invoice.reversed_entry_id = refunded_invoice_id.id

        set_reverse_entries(self)
        res = super()._post(soft)
        return res
