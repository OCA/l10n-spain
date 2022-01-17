# Copyright 2020 Binovo IT Human Project SL
# Copyright 2021 Landoo Sistemas de Informacion SL
# Copyright 2021 Digital5, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import SUPERUSER_ID, api

from odoo.addons.l10n_es_ticketbai_api.models.ticketbai_invoice import (
    RefundCode,
    RefundType,
)


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    fiscal_positions = env["account.fiscal.position"].search([])
    for position in fiscal_positions:
        if not position.company_id.chart_template_id:
            continue
        fiscal_position_template = env["account.fiscal.position.template"].search(
            [
                (
                    "chart_template_id",
                    "=",
                    env.ref("l10n_es.account_chart_template_common").id,
                ),
                ("name", "=", position.name),
            ]
        )
        if 1 == len(fiscal_position_template):
            vals = {}
            if fiscal_position_template.tbai_vat_regime_key:
                vals[
                    "tbai_vat_regime_key"
                ] = fiscal_position_template.tbai_vat_regime_key.id
            if fiscal_position_template.tbai_vat_regime_key2:
                vals[
                    "tbai_vat_regime_key2"
                ] = fiscal_position_template.tbai_vat_regime_key2.id
            if fiscal_position_template.tbai_vat_regime_key3:
                vals[
                    "tbai_vat_regime_key3"
                ] = fiscal_position_template.tbai_vat_regime_key3.id
            tbai_vat_exemptions = []
            for exemption in fiscal_position_template.tbai_vat_exemption_ids:
                tax = position.company_id.get_taxes_from_templates(exemption.tax_id)
                if 1 == len(tax):
                    tbai_vat_exemptions.append(
                        (
                            0,
                            0,
                            {
                                "tax_id": tax.id,
                                "tbai_vat_exemption_key": (
                                    exemption.tbai_vat_exemption_key.id
                                ),
                            },
                        )
                    )
            if len(tbai_vat_exemptions) > 0:
                vals["tbai_vat_exemption_ids"] = tbai_vat_exemptions
            if vals:
                position.write(vals)

    companies = env["res.company"].search([])

    for company in companies.filtered(lambda c: c.tbai_enabled):
        journals = env["account.journal"].search([("company_id", "=", company.id)])
        for journal in journals:
            if "sale" == journal.type:
                journal.refund_sequence = True

    invoices = env["account.move"].search(
        [("move_type", "in", ("out_invoice", "out_refund"))]
    )
    tbai_vat_regime_key_01 = env["tbai.vat.regime.key"].search(
        [("code", "=", "01")], limit=1
    )

    for invoice in invoices:
        invoice.tbai_vat_regime_key = (
            invoice.fiscal_position_id.tbai_vat_regime_key.id
            if invoice.fiscal_position_id
            else tbai_vat_regime_key_01.id
        )

        if invoice.move_type == "out_refund":
            invoice.tbai_refund_key = RefundCode.R1.value
            invoice.tbai_refund_type = RefundType.differences.value
