# Copyright 2025 Netkia Soluciones SLU - Carlos Sainz-Pardo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class L10nEsAeatTaxLine(models.Model):
    _inherit = "l10n.es.aeat.tax.line"

    map_line_id = fields.Many2one(required=False, ondelete="set null")
