# -*- encoding: utf-8 -*-

from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    informacion_catastral_ids = fields.One2many('informacion.catastral', 'partner_id')
    es_arrendatario = fields.Boolean('Es arrendatario')
    nif_representante_legal = fields.Char(string="Nif Representante Legal", size=9)