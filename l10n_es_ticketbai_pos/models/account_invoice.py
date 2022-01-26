# Copyright 2021 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    tbai_substitution_pos_order_id = fields.Many2one(
        comodel_name='pos.order', copy=False,
        help="Link between a validated Customer Invoice and its substitute.")

    def tbai_prepare_invoice_values(self):
        res = super().tbai_prepare_invoice_values()
        if self.tbai_substitute_simplified_invoice:
            refunded_pos_order = self.tbai_substitution_pos_order_id
            res.update({
                'is_invoice_refund': False,
                'tbai_invoice_refund_ids': [(0, 0, {
                    'number_prefix': refunded_pos_order.tbai_get_value_serie_factura(),
                    'number': refunded_pos_order.tbai_get_value_num_factura(),
                    'expedition_date':
                        refunded_pos_order.tbai_get_value_fecha_expedicion_factura()
                })]
            })
        return res
