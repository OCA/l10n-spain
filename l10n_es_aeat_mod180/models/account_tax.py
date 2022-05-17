# -*- encoding: utf-8 -*-

from odoo import _, api, fields, models

class AccountInvoiceLine(models.Model):
    _inherit = 'account.tax'

    def get_grouping_key(self, invoice_tax_val):
        res = super(AccountInvoiceLine, self).get_grouping_key(invoice_tax_val)
        if invoice_tax_val.get('informacion_catastral_id', False):
            res = res + '-' + str(invoice_tax_val['informacion_catastral_id'])
        return res

