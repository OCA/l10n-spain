# Copyright 2023 Moduon - Eduardo de Miguel
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class L10nEsAeatTownship(models.Model):
    _name = "l10n.es.aeat.township"
    _description = "Townships for AEAT"

    name = fields.Char()
    code = fields.Char()
    state_code = fields.Char(index=True)
