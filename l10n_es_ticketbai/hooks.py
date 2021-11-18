# Copyright 2020 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    fiscal_positions = env['account.fiscal.position'].search([])
    for position in fiscal_positions:
        if not position.company_id.chart_template_id:
            continue
        fiscal_position_template = env['account.fiscal.position.template'].search([
            ('chart_template_id', '=',
             env.ref('l10n_es.account_chart_template_common').id),
            ('name', '=', position.name)
        ])
        if 1 == len(fiscal_position_template):
            vals = {}
            if fiscal_position_template.tbai_vat_regime_key:
                vals['tbai_vat_regime_key'] = \
                    fiscal_position_template.tbai_vat_regime_key.id
            if fiscal_position_template.tbai_vat_regime_key2:
                vals['tbai_vat_regime_key2'] = \
                    fiscal_position_template.tbai_vat_regime_key2.id
            if fiscal_position_template.tbai_vat_regime_key3:
                vals['tbai_vat_regime_key3'] = \
                    fiscal_position_template.tbai_vat_regime_key3.id
            if 0 < len(fiscal_position_template.tbai_vat_exemption_ids):
                tbai_vat_exemptions = []
                for exemption in fiscal_position_template.tbai_vat_exemption_ids:
                    tax = env['l10n.es.aeat.report']\
                        .get_taxes_from_templates(exemption.tax_id)
                    if 1 == len(tax):
                        tbai_vat_exemptions.append((0, 0, {
                            'tax_id': tax.id,
                            'tbai_vat_exemption_key':
                                exemption.tbai_vat_exemption_key.id
                        }))
                if tbai_vat_exemptions:
                    vals['tbai_vat_exemption_ids'] = tbai_vat_exemptions
            if vals:
                position.write(vals)
