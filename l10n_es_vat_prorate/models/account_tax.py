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
    company_with_vat_prorate = fields.Boolean(
        related="company_id.with_vat_prorate",
        string="Company with VAT prorate",
    )

    @api.model
    def _get_vat_prorate_tax_types(self):
        """Odoo core tax types (``l10n_es_type``) of the deductible input VAT."""
        return [*self._l10n_es_get_sujeto_tax_types(), "dua"]

    def _is_vat_prorate_tax(self):
        """Deductible input VAT. IGIC is left out: model 303 only declares VAT, and
        the IGIC prorate is computed on the operations of the Canary Islands."""
        self.ensure_one()
        return (
            self.type_tax_use == "purchase"
            and self.amount_type == "percent"
            and self.amount > 0
            and self.l10n_es_type in self._get_vat_prorate_tax_types()
            and self.l10n_es_applicability != "03"
        )

    @api.depends(
        "company_id.with_vat_prorate",
        "type_tax_use",
        "l10n_es_type",
        "l10n_es_applicability",
    )
    def _compute_with_vat_prorate(self):
        """Only what defines the kind of tax recomputes the mark, so that the one
        set by the user in a tax survives the edition of its other fields.
        """
        for tax in self:
            tax.with_vat_prorate = (
                tax.company_with_vat_prorate and tax._is_vat_prorate_tax()
            )
