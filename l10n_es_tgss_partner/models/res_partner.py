# -*- coding: utf-8 -*-
# © 2015 Grupo ESOC Ingeniería de servicios, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = [
        _name,
        "l10n.es.tgss.contribution_account.company.abc",
        "l10n.es.tgss.contribution_account.person.abc",
        "l10n.es.tgss.contribution_group.abc",
        "l10n.es.tgss.professional_category.abc",
        "l10n.es.tgss.special_situations.abc",
        "l10n.es.tgss.study_level.abc",
    ]

    # Need this for the domain of ``contribution_account_id``
    contribution_account_owner_id = fields.Many2one(
        "res.partner",
        "Contribution account owner",
        compute="_compute_contribution_account_owner_id")

    # Need this to make this field work
    contribution_account_ids = fields.One2many(
        context={"default_owner_model": _name})

    @api.multi
    @api.depends("parent_id", "is_company")
    def _compute_contribution_account_owner_id(self):
        """Get closest parent company."""
        for s in self:
            company = s
            while company and not company.is_company:
                company = s.parent_id
            s.contribution_account_owner_id = company
