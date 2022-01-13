# Copyright 2022 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):

    _inherit = "res.company"

    with_vat_prorate = fields.Boolean()
    vat_prorate_ids = fields.One2many(
        "res.company.vat.prorate", inverse_name="company_id"
    )

    def get_prorate(self, date):
        self.ensure_one()
        prorate = self.env["res.company.vat.prorate"].search(
            [("company_id", "=", self.id), ("date", "<=", date)],
            order="date DESC",
            limit=1,
        )
        return prorate.vat_prorate


class ResCompanyVatProrate(models.Model):

    _name = "res.company.vat.prorate"
    _description = "VAT Prorate table"
    _rec_name = "date"
    _order = "date DESC"

    company_id = fields.Many2one("res.company", required=True)
    date = fields.Date(required=True, default=fields.Date.today())
    vat_prorate = fields.Float()
