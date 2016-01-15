# -*- coding: utf-8 -*-
# © 2015 Grupo ESOC Ingeniería de servicios, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, models


class ContributionGroup(models.Model):
    _description = "Spanish Social Security contribution groups"
    _name = "l10n.es.tgss.contribution_group"
    _inherit = "l10n.es.tgss.number_name"


class ABC(models.AbstractModel):
    _description = "Base for models linked to a contribution group"
    _name = "l10n.es.tgss.contribution_group.abc"

    contribution_group_id = fields.Many2one(
        "l10n.es.tgss.contribution_group",
        "Contribution group",
        ondelete="restrict")
