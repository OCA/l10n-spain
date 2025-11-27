# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    ine_code_id = fields.Many2one(
        comodel_name="res.ine.code",
        string="INE Code",
        help="National Statistics Institute code for the city. "
        "Start typing the city name to search.",
    )

    @api.onchange("city_id")
    def _onchange_city_id_ine_code(self):
        """Auto-establish INE code when city is selected."""
        if self.city_id:
            # Search for INE code linked to this city
            ine_code = self.env["res.ine.code"].search(
                [("city_id", "=", self.city_id.id)], limit=1
            )
            if ine_code:
                self.ine_code_id = ine_code
            else:
                # If no INE code found for this city, leave it empty
                self.ine_code_id = False
        else:
            # If city is cleared, also clear INE code
            self.ine_code_id = False
