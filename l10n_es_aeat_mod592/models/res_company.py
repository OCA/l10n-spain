# Copyright 2023 Nicolás Ramos - (https://binhex.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, _


class ResCompany(models.Model):

    _inherit = "res.company"

    company_plastic_type = fields.Selection([
        ('manufacturer', _('Manufacturer')),
        ('acquirer', _('Acquirer')),
        ('both', _('Both')),
    ], string='Company Plastic Type', default='acquirer')
