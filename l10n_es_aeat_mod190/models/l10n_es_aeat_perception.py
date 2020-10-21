# Copyright 2020 Creu Blanca
from odoo import fields, models


class L10nEsAeatReportPerceptionKey(models.Model):
    _name = 'l10n.es.aeat.report.perception.key'
    _description = 'Clave percepcion'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', size=3, required=True)
    aeat_number = fields.Char(string="Model number", size=3, required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    aeat_perception_subkey_id = fields.One2many(
        comodel_name='l10n.es.aeat.report.perception.subkey',
        inverse_name='aeat_perception_key_id', string='Subkeys',
        ondelete='cascade')
    additional_data_required = fields.Integer('Additional data required', default=0)


class L10nEsAeatReportPerceptionSubkey(models.Model):
    _name = 'l10n.es.aeat.report.perception.subkey'
    _description = 'Perception Subkey'

    aeat_perception_key_id = fields.Many2one(
        comodel_name='l10n.es.aeat.report.perception.key',
        oldname='perception_id',
        string='Perception ID')
    name = fields.Char(string='Name', size=2, required=True)
    aeat_number = fields.Char(string="Model number", size=3, required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    additional_data_required = fields.Integer('Additional data required', default=0)
