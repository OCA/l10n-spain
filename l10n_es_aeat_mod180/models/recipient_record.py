from odoo import fields, models


class RecipientRecord(models.Model):
    _name = "recipient.record"
    _description = "Recipient Record"

    report_id = fields.Many2one(
        "l10n.es.aeat.mod180.report", string="AEAT 180 Report", ondelete="cascade"
    )
    partner_id = fields.Many2one("res.partner", string="Empresa")
    l10n_es_aeat_real_estate_id = fields.Many2one(
        "l10n.es.aeat.real_estate", string="Información catastral"
    )
    sign = fields.Selection(
        selection=[(" ", "Positivo"), ("N", "Negativo")],
        string="Signo Base Retenciones",
    )
    retentions_base = fields.Float(
        string="Base retenciones e ingresos a cuenta", digits=(13, 2)
    )
    retentions_fee = fields.Float(
        string="Retenciones e ingresos a cuenta", digits=(13, 2)
    )
    retentions_percentage = fields.Float(string="% Retención", digits=(2, 2))
    accrual_year = fields.Integer(string="Ejercicio Devengo")
    base_move_line_ids = fields.Many2many(
        "account.move.line",
        "reg_perceptor_base_move_line_rel",
        "reg_perceptor_id",
        "move_line_id",
        string="Apuntes contable de base",
    )

    def action_get_base_move_lines(self):
        res = self.env.ref("account.action_account_moves_all_a").read()[0]
        view = self.env.ref("l10n_es_aeat_mod180.account_move_line_mod180_view_tree")
        res["views"] = [(view.id, "tree")]
        res["domain"] = [("id", "in", self.base_move_line_ids.ids)]
        return res
