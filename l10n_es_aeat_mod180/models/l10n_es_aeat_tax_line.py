# Copyright 2025 Netkia Soluciones SLU - Carlos Sainz-Pardo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class L10nEsAeatTaxLine(models.Model):
    _inherit = "l10n.es.aeat.tax.line"

    map_line_id = fields.Many2one(required=False, ondelete="set null")

    def get_calculated_move_lines(self):
        res = self.env.ref("account.action_account_moves_all_a").read()[0]
        view = self.env.ref("l10n_es_aeat.view_move_line_tree")
        res["views"] = [(view.id, "tree")]
        res["domain"] = [("id", "in", self.move_line_ids.ids)]
        return res
