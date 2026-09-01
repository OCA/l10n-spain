# Copyright 2022 Creu Blanca
# Copyright 2023 Tecnativa - Pedro M. Baeza
# Copyright 2024 Sygel - Manuel Regidor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models

from .prorate_taxes import PRORATE_TAXES


class AccountTax(models.Model):
    _inherit = "account.tax"

    with_vat_prorate = fields.Boolean(
        compute="_compute_with_vat_prorate",
        store=True,
        readonly=False,
        string="With VAT Prorate",
    )
    prorate_account_ids = fields.Many2many(
        "account.account",
        compute="_compute_with_vat_prorate",
        store=True,
        readonly=True,
        help="Accounts to apply the recompute",
    )
    company_with_vat_prorate = fields.Boolean(
        related="company_id.with_vat_prorate",
        string="Company with VAT prorate",
    )

    @api.depends("company_id.with_vat_prorate")
    def _compute_with_vat_prorate(self):
        for tax in self:
            with_vat_prorate = False
            prorate_account_ids = []
            if tax.company_with_vat_prorate and tax.get_external_id().get(tax.id):
                xml_id = (
                    tax.get_external_id()
                    .get(tax.id)
                    .split(f"account.{tax.company_id.id}_")[-1]
                )
                if xml_id in PRORATE_TAXES:
                    with_vat_prorate = True
                    if PRORATE_TAXES.get(xml_id).get("prorate_account_template_ids"):
                        prorate_taxes = self.company_id._get_prorate_accounts()
                        prorate_account_ids = [(5, 0, 0)]
                        for account_from_tmpl_id in prorate_taxes.get(xml_id).get(
                            "prorate_account_ids"
                        ):
                            prorate_account_ids.append((4, account_from_tmpl_id))
            tax.with_vat_prorate = with_vat_prorate
            tax.prorate_account_ids = prorate_account_ids
