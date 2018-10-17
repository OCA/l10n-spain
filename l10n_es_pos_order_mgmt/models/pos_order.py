# Copyright 2018 Tecnativa S.L. - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def _prepare_filter_query_for_pos(self, pos_session_id, query):
        res = super()._prepare_filter_query_for_pos(pos_session_id, query)
        res.append(('l10n_es_simplified_invoice_number', 'ilike', query))
        res[:0] = '|'
        return res

    @api.model
    def _prepare_fields_for_pos_list(self):
        res = super()._prepare_fields_for_pos_list()
        res.append('l10n_es_simplified_invoice_number')
        return res

    @api.multi
    def _prepare_done_order_for_pos(self):
        res = super()._prepare_done_order_for_pos()
        res.update({
            'simplified_invoice': self.l10n_es_simplified_invoice_number,
            'origin_simplified_invoice': (
                self.returned_order_id and
                self.returned_order_id.l10n_es_simplified_invoice_number),
        })
        return res
