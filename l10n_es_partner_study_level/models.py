# -*- encoding: utf-8 -*-

# Odoo, Open Source Management Solution
# Copyright (C) 2014-2015  Grupo ESOC <www.grupoesoc.es>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from openerp import fields, models


_NS = "l10n_es_partner_study_level"


class Level(models.Model):
    """Study levels."""
    _name = "%s.level" % _NS

    number = fields.Integer()
    name = fields.Char(translate=True)

    _sql_constraints = [
        ('number_unique', 'unique (number)', 'Each number must be unique.'),
        ('name_unique', 'unique (name)', 'Each name must be unique.'),
    ]


class StudyLevelModel(models.AbstractModel):
    """Models inheriting this ABC will be linked to a study level."""
    _name = "%s.abc" % _NS
    study_level = fields.Many2one(Level._name)


class Partner(models.Model):
    _name = "res.partner"
    _inherit = [_name, StudyLevelModel._name]
