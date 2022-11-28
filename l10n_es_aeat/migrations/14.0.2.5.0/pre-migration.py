# Copyright 2022 Studio73 - Guillermo Llinares <guillermo@studio73.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

xmlid_renames = [
    (
        "l10n_es_extra_data.{}_account_tax_template_s_iva5s",
        "l10n_es.{}_account_tax_template_s_iva5s",
    ),
    (
        "l10n_es_extra_data.{}_account_tax_template_p_iva5_sc",
        "l10n_es.{}_account_tax_template_p_iva5_sc",
    ),
]


@openupgrade.migrate()
def migrate(env, version):
    xmlid_renames_per_companies = []
    companies = env["res.company"].search([])
    for company_id in companies.ids:
        xmlid_renames_per_companies.append(
            (
                xmlid_renames[0][0].format(company_id),
                xmlid_renames[0][1].format(company_id),
            )
        )
        xmlid_renames_per_companies.append(
            (
                xmlid_renames[1][0].format(company_id),
                xmlid_renames[1][1].format(company_id),
            )
        )
    openupgrade.rename_xmlids(env.cr, xmlid_renames_per_companies)
