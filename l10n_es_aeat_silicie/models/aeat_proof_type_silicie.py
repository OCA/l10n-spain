# Copyright 2020 Javier de las Heras <jheras@alquemy.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AeatProofTypeSilicie(models.Model):
    _name = 'aeat.proof.type.silicie'
    _description = 'AEAT Proof Type SILICIE'

    code = fields.Char(
        required=True,
    )
    name = fields.Char(
        required=True,
    )
    description = fields.Char()

    def name_get(self):
        res = []
        for rec in self:
            name = "{} - {}".format(rec.code, rec.name)
            res.append((rec.id, name))
        return res

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        domain = args or []
        domain += ["|", ("name", operator, name), ("code", operator, name)]
        return self.search(domain, limit=limit).name_get()
