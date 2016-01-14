# -*- coding: utf-8 -*-
# © 2015 Grupo ESOC Ingeniería de servicios, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models


class Level(models.Model):
    """Study levels."""
    _name = "l10n_es_tgss.study_level"
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
    """Models inheriting this ABC will be linked to a study level."""
    _name = "l10n_es_tgss.study_level_abc"
    study_level_id = fields.Many2one(Level._name, "Study level")
