# -*- coding: utf-8 -*-
# © 2021 Binovo IT Human Project SL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import odoo


def migrate(cr, version):
    if not version:
        return
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    fp_nacional_domain = [('module', '=', 'l10n_es'),
                          ('model', '=', 'account.fiscal.position'),
                          ('name', 'ilike', '%fp_nacional%')]
    xmlids_fp_nacional = env['ir.model.data'].search(fp_nacional_domain)
    fp_nacional_tmpl = env.ref('l10n_es.fp_nacional')
    if fp_nacional_tmpl.tbai_vat_exemption_ids:
        for fp_tmpl_exemption in fp_nacional_tmpl.tbai_vat_exemption_ids:
            for xmlid_fp_nacional in xmlids_fp_nacional:
                vals = {}
                tbai_vat_exemptions = []
                fp_nacional = env.ref('l10n_es.' + xmlid_fp_nacional.name)
                if fp_nacional.company_id:
                    fp_tmpl_tax_id =\
                        env['l10n.es.aeat.report']._get_tax_id_from_tax_template(
                            fp_tmpl_exemption.tax_id, fp_nacional.company_id.id)
                    fp_tmpl_tax = \
                        env['account.tax'].browse(fp_tmpl_tax_id) \
                        if fp_tmpl_tax_id else False
                else:
                    fp_tmpl_tax =\
                        env['l10n.es.aeat.report']\
                        .get_taxes_from_templates(fp_tmpl_exemption.tax_id)
                if 1 == len(fp_tmpl_tax):
                    exemption_found = fp_nacional\
                        .tbai_vat_exemption_ids\
                        .filtered(lambda ex: ex.tax_id.id == fp_tmpl_tax.id)
                    if not exemption_found:
                        tbai_vat_exemptions.append((0, 0, {
                            'tax_id': fp_tmpl_tax.id,
                            'tbai_vat_exemption_key':
                                fp_tmpl_exemption.tbai_vat_exemption_key.id})
                        )
                if tbai_vat_exemptions:
                    vals['tbai_vat_exemption_ids'] = tbai_vat_exemptions
                    fp_nacional.write(vals)
