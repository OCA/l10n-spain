# -*- encoding: utf-8 -*-

from odoo import _, api, fields, models


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.multi
    @api.onchange('invoice_partner_id')
    def _compute_selectable_informacion_catastral_ids(self):
        for line in self:
            line.selectable_informacion_catastral_ids = []
            if line.invoice_partner_id:
                line.selectable_informacion_catastral_ids = line.invoice_partner_id.informacion_catastral_ids

    informacion_catastral_id = fields.Many2one('informacion.catastral')
    selectable_informacion_catastral_ids = fields.Many2many('informacion.catastral')
    invoice_partner_id = fields.Many2one('res.partner')
    es_arrendatario = fields.Boolean(related="invoice_partner_id.es_arrendatario")
