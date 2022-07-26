# Copyright 2017 Praxya (http://praxya.com/)
#                Daniel Rodriguez Lijo <drl.9319@gmail.com>
# Copyright 2017 ForgeFlow, S.L. <contact@forgeflow.com>
# Copyright 2019 Tecnativa - Carlos Dauden
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

from odoo import api, fields, models


class L10nEsVatBookLine(models.Model):
    _name = "l10n.es.vat.book.line"
    _description = "Spanish VAT book line"
    _order = "exception_text asc, entry_number asc, invoice_date asc, ref asc"

    def _selection_special_tax_group(self):
        return self.env["l10n.es.vat.book.line.tax"].fields_get(
            allfields=["special_tax_group"]
        )["special_tax_group"]["selection"]

    ref = fields.Char("Reference")
    entry_number = fields.Integer()
    external_ref = fields.Char("External Reference")

    line_type = fields.Selection(
        selection=[
            ("issued", "Issued"),
            ("received", "Received"),
            ("rectification_issued", "Refund Issued"),
            ("rectification_received", "Refund Received"),
        ],
    )
    invoice_date = fields.Date()

    partner_id = fields.Many2one(comodel_name="res.partner", string="Empresa")
    vat_number = fields.Char(string="NIF")

    vat_book_id = fields.Many2one(comodel_name="l10n.es.vat.book", string="Vat Book id")

    move_id = fields.Many2one(comodel_name="account.move", string="Invoice")

    move_id = fields.Many2one(comodel_name="account.move", string="Journal Entry")
    tax_line_ids = fields.One2many(
        comodel_name="l10n.es.vat.book.line.tax",
        inverse_name="vat_book_line_id",
        string="Tax Lines",
        copy=False,
    )

    exception_text = fields.Char()

    base_amount = fields.Float(
        string="Base",
    )
    total_amount = fields.Float(
        string="Total",
    )
    special_tax_group = fields.Selection(
        selection=_selection_special_tax_group,
        string="Special group",
        help="Special tax group as R.Eq, IRPF, etc",
    )

    @api.depends("tax_id")
    def _compute_tax_rate(self):
        for rec in self:
            rec.tax_rate = rec.tax_id.amount
