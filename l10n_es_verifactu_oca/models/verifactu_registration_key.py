# Copyright 2024 Aures TIC - Almudena de La Puente
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AeatVerifactuMappingRegistrationKeys(models.Model):
    _name = "verifactu.registration.key"
    _description = "VERI*FACTU registration key"

    code = fields.Char(required=True, size=2)
    name = fields.Char(required=True)
    verifactu_tax_key = fields.Selection(
        selection="_get_verifactu_tax_keys",
        string="VERI*FACTU tax key",
        required=True,
    )

    def name_get(self):
        return [(x.id, f"[{x.code}]-{x.name}") for x in self]

    @api.model
    def _get_verifactu_tax_keys(self):
        return self.env["account.fiscal.position"]._get_verifactu_tax_keys()
