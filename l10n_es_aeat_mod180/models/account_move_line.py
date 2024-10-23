from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.depends("move_id", "move_id.partner_id")
    def _compute_selectable_real_estate_ids(self):
        for line in self:
            line.selectable_real_estate_ids = []
            if line.move_id:
                line.selectable_real_estate_ids = (
                    line.move_id.partner_id.real_estate_ids
                )

    selectable_real_estate_ids = fields.Many2many(
        "l10n.es.aeat.real_estate", compute="_compute_selectable_real_estate_ids"
    )
