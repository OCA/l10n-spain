# -*- coding: utf-8 -*-
# Copyright 2017 FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, models, api


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    @api.model
    def _get_selection_sii_exempt_cause(self):
        return self.env['product.template'].fields_get(
            allfields=['sii_exempt_cause'])['sii_exempt_cause']['selection']

    @api.model
    def default_sii_exempt_cause(self):
        default_dict = self.env['product.template'].\
            default_get(['sii_exempt_cause'])
        return default_dict.get('sii_exempt_cause')

    sii_registration_key_sale = fields.Many2one(
        'aeat.sii.mapping.registration.keys',
        'Default SII Registration Key for Sales',
        domain=[('type', '=', 'sale')])
    sii_registration_key_purchase = fields.Many2one(
        'aeat.sii.mapping.registration.keys',
        'Default SII Registration Key for Purchases',
        domain=[('type', '=', 'purchase')])
    sii_active = fields.Boolean(
        string='SII Active', copy=False, default=True,
        help='Enable SII for this fiscal position?',
    )
    no_taxable_cause = fields.Selection(
        selection=[
            ('ImportePorArticulos7_14_Otros',
             'No sujeta - No sujeción artículo 7, 14, otros'),
            ('ImporteTAIReglasLocalizacion',
             'Operaciones no sujetas en el TAI por reglas de localización'),
        ], string="No taxable cause", default="ImportePorArticulos7_14_Otros",
    )
    sii_exempt_cause = fields.Selection(
        string="SII Exempt Cause",
        selection='_get_selection_sii_exempt_cause',
        default=default_sii_exempt_cause,
    )
