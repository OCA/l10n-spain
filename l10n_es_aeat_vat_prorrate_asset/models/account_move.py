# Copyright 2020 Tecnativa - Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    vat_prorrate_percent = fields.Float(string="Prorrate perc.", default=100)

    def _get_asset_analytic_values(self, vals, asset_vals):
        """Update assets values according prorrata.

        Although the method name is misleading, this effectively serves for
        changing the dictionary values before creating the asset.
        """
        vat_prorrate_percent = vals.get('vat_prorrate_percent', 100)
        if vat_prorrate_percent == 100 or not vals.get('asset_profile_id'):
            return
        taxes = self.env['account.tax']
        for command in vals.get('tax_ids', [(4, False)]):
            if command[0] == 4:
                taxes |= self.env['account.tax'].browse(command[1])
        totals = taxes.compute_all(asset_vals['purchase_value'])
        total_tax = totals['total_included'] - totals['total_excluded']
        increment = total_tax * (100 - vat_prorrate_percent) / 100
        asset_vals.update({
            'purchase_value': asset_vals['purchase_value'] + increment,
            'vat_prorrate_percent': vat_prorrate_percent,
            'vat_prorrate_increment': increment,
        })
