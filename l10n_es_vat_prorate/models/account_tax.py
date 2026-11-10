# Copyright 2022 Creu Blanca
# Copyright 2023 Tecnativa - Pedro M. Baeza
# Copyright 2024 Sygel - Manuel Regidor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models


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

    @api.model
    def _get_vat_prorate_tax_types(self):
        """Odoo core tax types (``l10n_es_type``) of the deductible input VAT."""
        return [*self._l10n_es_get_sujeto_tax_types(), "dua"]

    def _is_vat_prorate_tax(self):
        self.ensure_one()
        return (
            self.type_tax_use == "purchase"
            and self.amount_type == "percent"
            and self.amount > 0
            and self.l10n_es_type in self._get_vat_prorate_tax_types()
        )

    @api.depends(
        "company_id.with_vat_prorate",
        "type_tax_use",
        "amount_type",
        "amount",
        "l10n_es_type",
        "invoice_repartition_line_ids.factor_percent",
        "invoice_repartition_line_ids.account_id",
    )
    def _compute_with_vat_prorate(self):
        for tax in self:
            with_vat_prorate = (
                tax.company_with_vat_prorate and tax._is_vat_prorate_tax()
            )
            tax_lines = tax.invoice_repartition_line_ids.filtered(
                lambda line: line.repartition_type == "tax"
            )
            # A self-assessed tax (reverse charge, intra-community) has a negative
            # line for the output VAT: only the deductible side is prorated
            if with_vat_prorate and tax_lines.filtered(
                lambda line: line.factor_percent < 0
            ):
                tax.prorate_account_ids = tax_lines.filtered(
                    lambda line: line.factor_percent > 0
                ).account_id
            else:
                tax.prorate_account_ids = False
            tax.with_vat_prorate = with_vat_prorate
