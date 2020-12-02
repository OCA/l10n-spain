# Copyright 2020 Javier de las Heras <jheras@alquemy.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, _


class AeatUomSilicie(models.Model):
    _name = 'aeat.uom.silicie'
    _description = 'AEAT Epigraph SILICIE'

    code = fields.Char(
        string='Code',
    )

    name = fields.Char(
        string='Name',
    )

    def name_get(self):
        res = []
        for rec in self:
            name = u"{} - {}".format(rec.code, rec.name)
            res.append((rec.id, name))
        return res

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        domain = args or []
        domain += ["|", ("name", operator, name), ("code", operator, name)]
        return self.search(domain, limit=limit).name_get()
