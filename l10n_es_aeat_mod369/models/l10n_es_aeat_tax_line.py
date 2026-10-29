# Copyright 2022 Studio73 - Ethan Hildick <ethan@studio73.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class L10nEsAeatTaxLine(models.Model):
    _inherit = "l10n.es.aeat.tax.line"

    mod369_line_id = fields.Many2one(
        string="369 extra info", comodel_name="l10n.es.aeat.mod369.line"
    )

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for line in res:
            # Relate field both ways
            if not line.mod369_line_id:
                continue
            line.mod369_line_id.tax_line_id = line.id
        return res
