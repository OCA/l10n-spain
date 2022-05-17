# -*- encoding: utf-8 -*-

from odoo import fields, models, api, _


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.multi
    @api.depends('invoice_id', 'invoice_id.partner_id')
    def _compute_selectable_informacion_catastral_ids(self):
        for line in self:
            line.selectable_informacion_catastral_ids = []
            if line.invoice_id:
                line.selectable_informacion_catastral_ids = line.invoice_id.partner_id.informacion_catastral_ids

    informacion_catastral_id = fields.Many2one('informacion.catastral')
    selectable_informacion_catastral_ids = fields.Many2many('informacion.catastral', compute='_compute_selectable_informacion_catastral_ids')
    es_arrendatario = fields.Boolean(related="invoice_id.partner_id.es_arrendatario")
