# Copyright 2017 Praxya (http://praxya.com/)
#                Daniel Rodriguez Lijo <drl.9319@gmail.com>
# Copyright 2017 ForgeFlow, S.L. <contact@forgeflow.com>
# Copyright 2019 Tecnativa - Carlos Dauden
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

from odoo import api, fields, models


class L10nEsVatBookLineTax(models.Model):
    _name = "l10n.es.vat.book.line.tax"
    _description = "Spanish VAT book tax line"

    vat_book_line_id = fields.Many2one(
        comodel_name="l10n.es.vat.book.line",
        required=True,
        ondelete="cascade",
        index=True,
    )
    base_amount = fields.Float(string="Base")

    tax_id = fields.Many2one(comodel_name="account.tax", string="Tax")

    tax_rate = fields.Float(string="Tax Rate (%)", compute="_compute_tax_rate")

    tax_amount = fields.Float(string="Tax fee")

    total_amount = fields.Float(
        string="Total",
        compute="_compute_total_amount",
        store=True,
    )

    move_line_ids = fields.Many2many(
        comodel_name="account.move.line", string="Move Lines"
    )
    special_tax_group = fields.Selection(
        selection=[("req", "R.Eq."), ("irpf", "IRPF")],
        string="Special group",
        help="Special tax group as R.Eq, IRPF, etc",
    )
    special_tax_id = fields.Many2one(
        comodel_name="account.tax",
        string="Special Tax",
    )
    special_tax_amount = fields.Float(
        string="Special Tax fee",
    )
    total_amount_special_include = fields.Float(
        string="Total w/Special",
        compute="_compute_total_amount_special_include",
        store=True,
    )

    @api.depends("tax_id")
    def _compute_tax_rate(self):
        for rec in self:
            rec.tax_rate = rec.tax_id.amount

    @api.depends("base_amount", "tax_amount")
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = record.base_amount + record.tax_amount

    @api.depends("total_amount", "special_tax_amount")
    def _compute_total_amount_special_include(self):
        for record in self:
            record.total_amount_special_include = (
                record.total_amount + record.special_tax_amount
            )
