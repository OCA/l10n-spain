# -*- coding: utf-8 -*-
# Copyright 2017 FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, models


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    sii_registration_key_sale = fields.Many2one(
        'aeat.sii.mapping.registration.keys',
        'Default SII Registration Key for Sales',
        domain=[('type', '=', 'sale')])
    sii_registration_key_purchase = fields.Many2one(
        'aeat.sii.mapping.registration.keys',
        'Default SII Registration Key for Purchases',
        domain=[('type', '=', 'purchase')])
