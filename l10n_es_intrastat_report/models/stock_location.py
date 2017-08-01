# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models


class StockLocation(models.Model):
    _inherit = 'stock.location'

    @api.multi
    def get_intrastat_state(self):
        self.ensure_one()
        locations = self.search(
            [('parent_left', '<=', self.parent_left),
             ('parent_right', '>=', self.parent_right)])
        warehouses = self.env['stock.warehouse'].search([
            ('lot_stock_id', 'in', [x.id for x in locations]),
            ('partner_id.state_id', '!=', False)])
        if warehouses:
            return warehouses[0].partner_id.state_id
        return None
