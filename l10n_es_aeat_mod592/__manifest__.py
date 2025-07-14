# Copyright 2014-2022 Nicolás Ramos (http://binhex.es)
# Copyright 2023 Binhex System Solutions
# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "AEAT modelo 592",
    "version": "15.0.2.0.1",
    "category": "Accounting",
    "author": "Tecnativa, Binhex System Solutions, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": ["l10n_es_aeat", "report_csv", "report_xlsx", "stock"],
    "data": [
        "data/ir_sequence_data.xml",
        "security/aeat_security.xml",
        "security/ir.model.access.csv",
        "views/product_template_views.xml",
        "views/res_partner_views.xml",
        "views/mod592_views.xml",
        "views/mod592_acquirer_line_views.xml",
        "views/mod592_manufacturer_line_views.xml",
        "views/res_company_views.xml",
        "report/aeat_mod592.xml",
        "report/common_templates.xml",
        "report/report_views.xml",
    ],
    "development_status": "Beta",
    "installable": True,
}
