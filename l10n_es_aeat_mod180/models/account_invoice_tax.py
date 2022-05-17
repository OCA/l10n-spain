# -*- encoding: utf-8 -*-

from odoo import _, api, fields, models


class AccountInvoiceTax(models.Model):
    _inherit = 'account.invoice.tax'

    informacion_catastral_id = fields.Many2one('informacion.catastral')

