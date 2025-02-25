# Copyright 2017 MINORISA (http://www.minorisa.net)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AeatSiiMappingRegistrationKeys(models.Model):
    _name = "aeat.sii.mapping.registration.keys"
    _description = "Aeat SII Invoice Registration Keys"

    code = fields.Char(required=True, size=2)
    name = fields.Char(required=True)
    type = fields.Selection(
        selection=[("sale", "Sale"), ("purchase", "Purchase")],
        required=True,
    )

    @api.depends("name", "code")
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"[{record.code}]-{record.name}"
