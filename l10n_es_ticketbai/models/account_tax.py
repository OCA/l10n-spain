# Copyright 2020 Binovo IT Human Project SL
# Copyright 2021 Digital5, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class AccountTax(models.Model):
    _inherit = 'account.tax'

    tbai_vat_regime_simplified = fields.Boolean(
        "Regime Simplified",
        compute="_compute_tbai_vat_regime_simplified",
        store=True,
        readonly=False,
        help="Change default value for tax individually behavior",
    )

    @api.depends("company_id.tbai_vat_regime_simplified")
    def _compute_tbai_vat_regime_simplified(self):
        for tax in self:
            tax.tbai_vat_regime_simplified = (
                tax.company_id.tbai_enabled
                and tax.company_id.tbai_vat_regime_simplified
                or False
            )

    def tbai_is_subject_to_tax(self):
        s_iva_ns_tbai_maps = self.env["tbai.tax.map"].search(
            [('code', 'in', ("SNS", "BNS"))]
        )
        s_iva_ns_taxes = self.company_id.get_taxes_from_templates(
            s_iva_ns_tbai_maps.mapped("tax_template_ids")
        )
        return self not in s_iva_ns_taxes

    def tbai_is_tax_exempted(self):
        map_ids = self.env["tbai.tax.map"].search([("code", "in", ["IEE", "SER"])])
        tax_ids = self.company_id.get_taxes_from_templates(map_ids.mapped("tax_template_ids"))
        return self in tax_ids

    def tbai_is_not_tax_exempted(self):
        map_ids = self.env["tbai.tax.map"].search([("code", "in", ["IEE", "SER"])])
        tax_ids = self.company_id.get_taxes_from_templates(map_ids.mapped("tax_template_ids"))
        return self not in tax_ids
