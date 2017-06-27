# -*- coding: utf-8 -*-

from openerp import fields, models, api

class AccountPeriod(models.Model):
    _inherit = 'account.period'
    
    vat_prorrate_percent = fields.Float(string="VAT prorrate percentage", default=100)