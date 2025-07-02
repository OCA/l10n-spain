# Copyright 2021 Binovo IT Human Project SL
# Copyright 2022 Landoo Sistemas de Informacion SL
# Copyright 2022 Advanced Programming Solutions SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import Command, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    tbai_substitution_pos_order_id = fields.Many2one(
        comodel_name="pos.order",
        copy=False,
        help="Link between a validated Customer Invoice and its substitute.",
    )

    def tbai_prepare_invoice_values(self):
        res = super().tbai_prepare_invoice_values()
        if self.tbai_substitute_simplified_invoice:
            refunded_pos_order = self.tbai_substitution_pos_order_id
            res.update(
                {
                    "is_invoice_refund": False,
                    "tbai_invoice_refund_ids": [
                        Command.create(
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
                            }
                        )
                    ],
                }
            )
        return res

    # For Ticketbai is mandatory to specify origin invoice in refunds
    def _post(self, soft=True):
        for pos_order in (
            self.sudo().mapped("pos_order_ids").filtered("refunded_order_ids")
        ):
            refunded_order = pos_order.refunded_order_ids[0]
            pos_order.reversed_entry_id = refunded_order.account_move.id

        res = super()._post(soft)
        return res
