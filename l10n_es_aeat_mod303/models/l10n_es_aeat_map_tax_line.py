# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models
from odoo.fields import Domain


class L10nEsAeatMapTaxLine(models.Model):
    _inherit = "l10n.es.aeat.map.tax.line"

    tax_tag_expression_id = fields.Many2one(
        comodel_name="account.report.expression",
        string="Tax report expression",
        ondelete="set null",
        help="Besides the taxes of the chart template, take the taxes of the company "
        "whose repartition lines carry the tags of this expression of the Odoo tax "
        "report, as the ones that Odoo creates without a chart template identifier.",
    )

    def get_taxes_for_company(self, company):
        taxes = super().get_taxes_for_company(company)
        tags = self.tax_tag_expression_id._get_matching_tags()
        if tags:
            tax_model = self.env["account.tax"].with_context(active_test=False)
            taxes |= tax_model.search(
                Domain(tax_model._check_company_domain(company))
                & Domain("repartition_line_ids.tag_ids", "in", tags.ids)
            )
        return taxes
