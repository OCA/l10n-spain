# Copyright 2017 FactorLibre - Janire Olagibel
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class EcoembesSubmaterial(models.Model):
    _name = "ecoembes.submaterial"
    _description = "Submaterial"
    _inherit = "abstract.ecoembes.mixin"

    name = fields.Char(string="Submaterial")
    material_id = fields.Many2one(
        comodel_name="ecoembes.material", string="Material", required=True
    )

    def name_get(self):
        res = []
        for obj in self:
            if obj.material_id:
                res.append((obj.id, "{} - {}".format(obj.material_id.name, obj.name)))
            else:
                res.append((obj.id, obj.name))
        return res
