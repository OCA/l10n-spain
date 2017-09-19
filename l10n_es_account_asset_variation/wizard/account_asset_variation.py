# -*- coding: utf-8 -*-
# Copyright 2017 Ainara Galdona - AvanzOSC
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api


class AccountAssetVariation(models.TransientModel):

    _name = 'account.asset.variation'

    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    percentage = fields.Integer(string='Percentage', required=True)

    @api.multi
    def action_calculate_depreciation_board(self):
        self.ensure_one()
        asset_id = self.env.context.get('active_id')
        asset = self.env['account.asset.asset'].browse(asset_id)
        asset.with_context(wiz=self).compute_depreciation_board()
        return True
