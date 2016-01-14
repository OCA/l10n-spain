# -*- coding: utf-8 -*-
# © 2015 Grupo ESOC Ingeniería de servicios, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models


class ProfessionalCategory(models.Model):
    """Professional categories."""
    _name = "l10n_es_tgss.professional_category"
    _rec_name = "combined"

    number = fields.Integer()
    name = fields.Char(translate=True)
    combined = fields.Char(compute="_combined_compute")

    _sql_constraints = [
        ('number_unique', 'unique (number)', 'Each number must be unique.'),
        ('name_unique', 'unique (name)', 'Each name must be unique.'),
    ]

    @api.one
    @api.depends("number", "name")
    def _combined_compute(self):
        self.combined = "%d. %s" % (self.number, self.name)


class ABC(models.AbstractModel):
    """Models inheriting this ABC will be linked to a professional category."""
    _name = "l10n_es_tgss.professional_category_abc"
    professional_category_id = fields.Many2one(
        ProfessionalCategory._name,
        "Professional category")
