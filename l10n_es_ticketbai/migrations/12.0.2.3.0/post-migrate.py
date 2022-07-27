# -*- coding: utf-8 -*-
# © 2021 Binovo IT Human Project SL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import odoo


def migrate(cr, version):
    if not version:
        return
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    fp_nacional_tmpl = env.ref('l10n_es.fp_nacional')
    if fp_nacional_tmpl.tbai_vat_exemption_ids:
        vals = {}
        tbai_vat_exemptions = []
        for fp_tmpl_exemption in fp_nacional_tmpl.tbai_vat_exemption_ids:
            fp_tmpl_tax = env['l10n.es.aeat.report']\
                .get_taxes_from_templates(fp_tmpl_exemption.tax_id)
            tbai_vat_exemptions.append((0, 0, {
                'tax_id': fp_tmpl_tax.id,
                'tbai_vat_exemption_key':
                    fp_tmpl_exemption.tbai_vat_exemption_key.id})
            )