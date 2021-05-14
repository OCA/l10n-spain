# Copyright 2021 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields, _


class TicketBaiInstallation(models.Model):
    _name = 'tbai.installation'

    name = fields.Char(
        string='Software Name', required=True, copy=False,
        help="Registered name at the Tax Agency.")
    developer_id = fields.Many2one(
        comodel_name='res.partner', string='Developer', required=True, copy=False)
    vat = fields.Char('TIN', related='developer_id.vat')
    license_key = fields.Char('License Key', required=True, copy=False)
    version = fields.Char(
        string='Software Version', required=True, copy=False,
        help="Version of the software.")

    _sql_constraints = [
        ('name_ref_uniq', 'UNIQUE(name)', _('Software Name must be unique!')),
        ('developer_ref_uniq', 'UNIQUE(developer_id)', _('Developer must be unique!')),
        ('license_ref_uniq', 'UNIQUE(license_key)', _('License Key must be unique!')),
    ]
