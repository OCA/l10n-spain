# Copyright 2025 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    sigaus_subject = fields.Boolean(string="Subject To SIGAUS", default=True)

    def _commercial_fields(self):
        fields = super()._commercial_fields()
        fields += ["sigaus_subject"]
        return fields
