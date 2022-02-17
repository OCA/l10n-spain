# Copyright 2019 Acysos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    vat_check_aeat = fields.Boolean(string="Verify AEAT Partner Data")
