# Copyright 2022 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, tools


class ResCompany(models.Model):

    _inherit = "res.company"

    with_vat_prorate = fields.Boolean()
    vat_prorate_ids = fields.One2many(
        "res.company.vat.prorate", inverse_name="company_id"
    )
    prorrate_asset_account_id = fields.Many2one(
        "account.account",
        domain="[('company_id', '=', id)]",
        compute="_compute_prorrate_accounts",
        store=True,
        readonly=False,
    )
    prorrate_investment_account_id = fields.Many2one(
        "account.account",
        domain="[('company_id', '=', id)]",
        compute="_compute_prorrate_accounts",
        store=True,
        readonly=False,
    )

    @api.depends("chart_template_id", "with_vat_prorate")
    def _compute_prorrate_accounts(self):
        for record in self:
            if record.with_vat_prorate and record.chart_template_id:
                record.prorrate_asset_account_id = self.env.ref(
                    "l10n_es.%s_account_common_6341" % record.id,
                    raise_if_not_found=False,
                )
                record.prorrate_investment_account_id = self.env.ref(
                    "l10n_es.%s_account_common_6342" % record.id,
                    raise_if_not_found=False,
                )
            else:
                record.prorrate_asset_account_id = False
                record.prorrate_investment_account_id = False

    def get_prorate(self, date):
        self.ensure_one()
        prorate = self.env["res.company.vat.prorate"].search(
            [("company_id", "=", self.id), ("date", "<=", date)],
            order="date DESC",
            limit=1,
        )
        return prorate.vat_prorate

    @tools.ormcache(
        "self.id",
        "self.prorrate_asset_account_id.id",
        "self.prorrate_investment_account_id.id",
    )
    def _get_tax_prorrate_account_map(self):
        """Get the account mapping according user type"""
        return {
            self.env.ref(
                "account.data_account_type_current_assets"
            ).id: self.prorrate_asset_account_id.id,
            self.env.ref(
                "account.data_account_type_non_current_assets"
            ).id: self.prorrate_asset_account_id.id,
            self.env.ref(
                "account.data_account_type_fixed_assets"
            ).id: self.prorrate_asset_account_id.id,
            self.env.ref(
                "account.data_account_type_current_liabilities"
            ).id: self.prorrate_investment_account_id.id,
            self.env.ref(
                "account.data_account_type_non_current_liabilities"
            ).id: self.prorrate_investment_account_id.id,
        }


class ResCompanyVatProrate(models.Model):

    _name = "res.company.vat.prorate"
    _description = "VAT Prorate table"
    _rec_name = "date"
    _order = "date DESC"

    company_id = fields.Many2one("res.company", required=True)
    date = fields.Date(required=True, default=fields.Date.today())
    vat_prorate = fields.Float()
