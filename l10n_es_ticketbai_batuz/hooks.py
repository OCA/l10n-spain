# Copyright 2021 Digital5, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import SUPERUSER_ID, api


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
            if fiscal_position_template.tbai_vat_regime_purchase_key:
                vals[
                    "tbai_vat_regime_purchase_key"
                ] = fiscal_position_template.tbai_vat_regime_purchase_key.id
            if fiscal_position_template.tbai_vat_regime_purchase_key2:
                vals[
                    "tbai_vat_regime_purchase_key2"
                ] = fiscal_position_template.tbai_vat_regime_purchase_key2.id
            if fiscal_position_template.tbai_vat_regime_purchase_key3:
                vals[
                    "tbai_vat_regime_purchase_key3"
                ] = fiscal_position_template.tbai_vat_regime_purchase_key3.id
            if vals:
                position.write(vals)
