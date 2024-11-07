# Copyright 2024 Aures TIC - Almudena de La Puente <almudena@aurestic.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AeatVerifactuMappingRegistrationKeys(models.Model):
    _name = "aeat.verifactu.registration.keys"
    _description = "Aeat Verifactu Registration Keys"

    code = fields.Char(required=True, size=2)
    name = fields.Char(required=True)
    verifactu_tax_key = fields.Selection(
        selection="_get_verifactu_tax_keys",
        required=True,
    )

    def name_get(self):
        vals = []
        for record in self:
            name = "[{}]-{}".format(record.code, record.name)
            vals.append(tuple([record.id, name]))
        return vals

    @api.model
    def _get_verifactu_tax_keys(self):
        return self.env["account.fiscal.position"]._get_verifactu_tax_keys()
