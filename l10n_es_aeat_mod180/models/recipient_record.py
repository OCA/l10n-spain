# Copyright 2025 Netkia Soluciones SLU - Carlos Sainz-Pardo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


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
    representative_vat = fields.Char(
        string="Representative VAT",
        size=9,
        help="VAT number of the legal representative of the recipient",
        compute="_compute_representative_vat",
        store=True,
        readonly=False,
    )

    @api.depends("l10n_es_aeat_real_estate_id.representative_vat", "partner_id.vat")
    @api.onchange("l10n_es_aeat_real_estate_id", "partner_id")
    def _compute_representative_vat(self):
        for record in self:
            if (
                record.partner_id.vat
                != record.l10n_es_aeat_real_estate_id.representative_vat
            ):
                record.representative_vat = (
                    record.l10n_es_aeat_real_estate_id.representative_vat
                )
            else:
                record.representative_vat = ""

            record.l10n_es_aeat_real_estate_id._compute_real_estate_situation()

    def action_get_base_move_lines(self):
        res = self.env.ref("account.action_account_moves_all_a").read()[0]
        view = self.env.ref("l10n_es_aeat.view_move_line_tree")
        res["views"] = [(view.id, "tree")]
        res["domain"] = [("id", "in", self.base_move_line_ids.ids)]
        return res
