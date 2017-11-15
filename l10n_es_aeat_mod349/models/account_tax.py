# -*- coding: utf-8 -*-
# Copyright 2017 Luis M. Ontalba <luis.martinez@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields


class AccountTaxTemplate(models.Model):
    _inherit = 'account.tax.template'

    aeat_349_operation_key = fields.Many2one(
        string='AEAT 349 Operation key',
        comodel_name='aeat.349.map.line',
    )


class AccountTax(models.Model):
    _inherit = 'account.tax'

    aeat_349_operation_key = fields.Many2one(
        string='AEAT 349 Operation key',
        comodel_name='aeat.349.map.line',
        compute='_compute_aeat_349_operation_key',
    )

    @api.depends('name', 'description')
    def _compute_aeat_349_operation_key(self):
        map_349 = self.env['aeat.349.map.line'].search([])
        for tax in self:
            for line in map_349:
                for tax_template in line.taxes:
                    if (tax.name == tax_template.name) or (
                                tax.description == tax_template.name):
                        tax.aeat_349_operation_key = line
