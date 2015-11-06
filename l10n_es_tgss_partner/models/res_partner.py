# -*- coding: utf-8 -*-
# © 2015 Grupo ESOC Ingeniería de servicios, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, models
from .common import M


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = [_name, "l10n_es_tgss.full_abc"]

    contribution_account_ids = fields.One2many(
        M % "contribution_account")
    contribution_account_id = fields.Many2one(
        M % "contribution_account")
    affiliation_number_id = fields.Many2one(
        M % "contribution_account")
