# -*- coding: utf-8 -*-
# Copyright 2015-2017 Tecnativa - Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import fields, models


class L10nEsAeatMod303Report(models.Model):
    _inherit = 'l10n.es.aeat.mod303.report'

    def _calculate_casilla_44(self):
        super(L10nEsAeatMod303Report, self)._calculate_casilla_44()
        year = fields.Date.from_string(self.fiscalyear_id.date_start).year
        assets = self.env['account.asset.asset'].search(
            [('purchase_date', 'like', '{}%'.format(year))]
        )
        for asset in assets.filtered('vat_prorrate_percent'):
            original_taxes = (
                asset.vat_prorrate_increment * 100 /
                (100 - asset.vat_prorrate_percent)
            )
            real_increment = (
                original_taxes * (100 - self.vat_prorrate_percent) / 100
            )
            self.casilla_44 += asset.vat_prorrate_increment - real_increment
