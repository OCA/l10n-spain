# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
import odoo.addons.decimal_precision as dp
from odoo.tools import float_compare


class PosOrder(models.Model):
    _inherit = 'pos.order'

    l10n_es_simplified_invoice_number = fields.Char(
        'Simplified invoice',
        copy=False,
        oldname='simplified_invoice',
    )

    @api.model
    def _simplified_limit_check(self, amount_total, limit=3000):
        precision_digits = dp.get_precision('Account')(self.env.cr)[1]
        # -1 or 0: amount_total <= limit, simplified
        #       1: amount_total > limit, can not be simplified
        return float_compare(
            amount_total, limit, precision_digits=precision_digits) < 0

    @api.model
    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)
        res.update({
            'l10n_es_simplified_invoice_number': ui_order.get(
                'simplified_invoice', ''),
        })
        return res

    @api.model
    def _process_order(self, pos_order):
        simplified_invoice_number = pos_order.get('simplified_invoice', '')
        if not simplified_invoice_number:
            return super(PosOrder, self)._process_order(pos_order)
        pos_order_obj = self.env['pos.order']
        pos = self.env['pos.session'].browse(
            pos_order.get('pos_session_id')).config_id
        if pos_order_obj._simplified_limit_check(
                pos_order.get('amount_total'),
                pos.l10n_es_simplified_invoice_limit):
            pos_order.update({
                'l10n_es_simplified_invoice_number': simplified_invoice_number,
            })
            sequence = pos.l10n_es_simplified_invoice_sequence_id
            sequence.number_next_actual = int(
                simplified_invoice_number.replace(
                    pos.l10n_es_simplified_invoice_prefix, '')) + 1
        return super(PosOrder, self)._process_order(pos_order)
