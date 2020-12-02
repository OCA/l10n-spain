# Copyright 2020 Javier de las Heras <jheras@alquemy.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, _


class AeatEpigraphSilicie(models.Model):
    _name = 'aeat.epigraph.silicie'
    _description = 'AEAT Epigraph SILICIE'

    code = fields.Char(
        string='Code',
    )

    name = fields.Char(
        string='Name',
    )

    tax_silicie_alcohol = fields.Boolean(
        string='Alcohol',
    )

    tax_silicie_beer = fields.Boolean(
        string='Beer',
    )

    tax_silicie_intermediate = fields.Boolean(
        string='Intermediate',
    )

    tax_silicie_intermediate_art = fields.Boolean(
        string='Intermediate Art. 32 LIE',
    )

    tax_silicie_wine = fields.Boolean(
        string='Wine',
    )

    tax_silicie_vinegar = fields.Boolean(
        string='Vinegar',
    )

    tax_silicie_hydrocarbons = fields.Boolean(
        string='Hydrocarbons',
    )

    tax_silicie_tobacco = fields.Boolean(
        string='Tobacco',
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
