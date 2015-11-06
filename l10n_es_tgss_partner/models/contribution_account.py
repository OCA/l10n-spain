# -*- coding: utf-8 -*-
# © 2015 Grupo ESOC Ingeniería de servicios, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, models
from .common import M


class ContributionAccount(models.Model):
    _name = M % "contribution_account"
    _inherit = "l10n_es_tgss.contribution_account_abc"

    owner_id = fields.Many2one("res.partner")
