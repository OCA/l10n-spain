# Copyright 2020 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields, api


class TicketBaiGeneralInfo(models.TransientModel):
    _name = 'tbai.info'

    tbai_enabled = fields.Boolean(
        default=lambda self: self.env.user.company_id.tbai_enabled)
    name = fields.Char(string='Developer', compute='_compute_name')
    company_id = fields.Many2one(
        comodel_name='res.company', string='Company', readonly=True,
        default=lambda self: self.env.user.company_id)
    developer_id = fields.Many2one(
        comodel_name='res.partner', string='Developer',
        related='company_id.tbai_developer_id', readonly=True)
    software = fields.Char(string='Software', compute='_compute_software')
    device_serial_number = fields.Char(
        'Device Serial Number', compute='_compute_device_serial_number')

    @api.multi
    @api.depends('developer_id', 'developer_id.vat', 'developer_id.name')
    def _compute_name(self):
        for record in self:
            record.name = "(%s) %s" % (
                record.developer_id.vat, record.developer_id.name)

    @api.multi
    @api.depends('company_id')
    def _compute_software(self):
        for record in self:
            software_version = self.sudo().env['ir.module.module'].search([
                ('name', '=', 'l10n_es_ticketbai')]).latest_version
            record.software = "(%s) %s" % (
                software_version, record.company_id.tbai_software_name)

    @api.multi
    @api.depends('company_id')
    def _compute_device_serial_number(self):
        for record in self:
            record.device_serial_number = record.company_id.tbai_device_serial_number
