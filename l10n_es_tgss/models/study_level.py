# -*- coding: utf-8 -*-
# © 2015 Grupo ESOC Ingeniería de servicios, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, models


class StudyLevel(models.Model):
    _description = "Spanish Social Security study levels"
    _name = "l10n.es.tgss.study_level"
    _inherit = "l10n.es.tgss.number_name"


class ABC(models.AbstractModel):
    _description = "Base for models linked to a study level"
    _name = "l10n.es.tgss.study_level.abc"

    study_level_id = fields.Many2one(
        "l10n.es.tgss.study_level",
        "Study level",
        ondelete="restrict")
