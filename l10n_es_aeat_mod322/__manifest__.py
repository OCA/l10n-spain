# Copyright 2022 Jan Tugores Castells (QubiQ)
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

{
    "name": "AEAT modelo 322",
    "version": "15.0.2.3.0",
    "category": "Accounting",
    # "development_status": "Mature",
    "author": "QubiQ" "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": [
        "account_chart_update",
        "base",
        "l10n_es",
        "l10n_es_aeat",
    ],
    "data": [
        "data/account_fiscal_position_template_data.xml",
        "data/account_tax_group_data.xml",
        "data/account_tax_data.xml",
        "data/tax_code_map_mod322_data.xml",
        "data/aeat_export_mod322_data.xml",
        "data/l10n_es_aeat_mod322_report_activity_code_data.xml",
        "views/l10n_es_aeat_mod322_report_activity_code_data_views.xml",
        "views/mod322_view.xml",
        "views/res_company_view.xml",
        "security/l10n_es_aeat_mod322_security.xml",
        "security/ir.model.access.csv",
    ],
    "maintainers": [],
    "installable": True,
}
