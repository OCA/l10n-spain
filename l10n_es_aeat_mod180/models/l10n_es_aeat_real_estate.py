# Copyright 2023 Moduon - Eduardo de Miguel
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class L10nEsAeatRealEstate(models.Model):
    _inherit = "l10n.es.aeat.real_estate"

    real_estate_situation = fields.Selection(
        [("1", "01"), ("2", "02"), ("3", "03"), ("4", "04")], required=True
    )

    @api.onchange("postal_code", "reference")
    def _onchange_postal_code(self):

        if not self.reference:
            real_estate_situation = "4"
        elif self.postal_code:
            # Situacion inmueble
            if (
                self.state_id
                and self.state_id.code
                and self.state_id.code not in ["NA", "BI", "SS", "VI"]
            ):
                real_estate_situation = "1"
            elif (
                self.state_id
                and self.state_id.code
                and self.state_id.code in ["BI", "SS", "VI"]
            ):
                real_estate_situation = "2"
            elif self.state_id and self.state_id.code and self.state_id.code == "NA":
                real_estate_situation = "3"
        self.update({"real_estate_situation": real_estate_situation})
