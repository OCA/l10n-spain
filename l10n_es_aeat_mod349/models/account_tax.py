# -*- coding: utf-8 -*-
# Copyright 2017 Luis M. Ontalba <luis.martinez@tecnativa.com>
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openerp import api, models, fields


class AccountTax(models.Model):
    _inherit = 'account.tax'

    def _selection_operation_key(self):
        return self.env['account.move.line'].fields_get(
            allfields=['l10n_es_aeat_349_operation_key'],
        )['l10n_es_aeat_349_operation_key']['selection']

    l10n_es_aeat_349_operation_key = fields.Selection(
        selection=_selection_operation_key,
        string='AEAT 349 Operation key',
        compute='_compute_l10n_es_aeat_349_operation_key',
    )

    @api.depends('name', 'description')
    def _compute_l10n_es_aeat_349_operation_key(self):
        map_349 = self.env['aeat.349.map.line'].search([])
        for tax in self:
            for line in map_349:
                if any([tax.name == tmpl.name or tax.description == tmpl.name
                        for tmpl in line.tax_tmpl_ids]):
                    tax.l10n_es_aeat_349_operation_key = line.operation_key
                    break
