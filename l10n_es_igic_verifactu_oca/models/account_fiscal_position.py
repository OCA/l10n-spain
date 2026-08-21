# Copyright 2026 - OCA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models

ATC_VERIFACTU_TAX_KEY = "03"


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    verifactu_tax_key = fields.Selection(
        selection="_get_verifactu_tax_keys",
        default=lambda self: self._default_verifactu_tax_key(),
        string="VERI*FACTU tax key",
    )

    @api.model
    def _default_verifactu_tax_key(self):
        agency = self.env.ref(
            "l10n_es_aeat.aeat_tax_agency_canarias", raise_if_not_found=False
        )
        if agency and self.env.company.tax_agency_id == agency:
            return ATC_VERIFACTU_TAX_KEY
        return "01"

    @api.model_create_multi
    def create(self, vals_list):
        agency = self.env.ref(
            "l10n_es_aeat.aeat_tax_agency_canarias", raise_if_not_found=False
        )
        if agency:
            for vals in vals_list:
                if vals.get("verifactu_tax_key"):
                    continue
                company_id = vals.get("company_id") or self.env.company.id
                company = self.env["res.company"].browse(company_id)
                if company.tax_agency_id == agency:
                    vals["verifactu_tax_key"] = ATC_VERIFACTU_TAX_KEY
        return super().create(vals_list)
