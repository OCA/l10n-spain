from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.depends("move_id", "move_id.partner_id")
    def _compute_selectable_informacion_catastral_ids(self):
        for line in self:
            line.selectable_informacion_catastral_ids = []
            if line.move_id:
                line.selectable_informacion_catastral_ids = (
                    line.move_id.partner_id.informacion_catastral_ids
                )

    informacion_catastral_id = fields.Many2one("informacion.catastral")
    selectable_informacion_catastral_ids = fields.Many2many(
        "informacion.catastral", compute="_compute_selectable_informacion_catastral_ids"
    )
    es_arrendatario = fields.Boolean(related="move_id.partner_id.es_arrendatario")

    def get_grouping_key(self, invoice_tax_val):
        res = super().get_grouping_key(invoice_tax_val)
        if invoice_tax_val.get("informacion_catastral_id", False):
            res = res + "-" + str(invoice_tax_val["informacion_catastral_id"])
        return res
