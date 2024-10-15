# Copyright 2014-2022 Nicolás Ramos (http://binhex.es)
# Copyright 2023 Binhex System Solutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "AEAT modelo 592",
    "version": "14.0.1.0.0",
    "category": "Localisation/Accounting",
    "author": "Binhex System Solutions, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": [
        "product", "account", "stock", "mrp", "l10n_es",
        "l10n_es_aeat", "report_xlsx", "report_csv"],
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        "views/product_template.xml",
        "views/product_template.xml",
        "views/res_partner.xml",
        "views/mod592_view.xml",
        "views/mod592_acquirer_line_view.xml",
        "views/mod592_manufacturer_line_view.xml",
        "views/res_company.xml",
        "report/aeat_mod592.xml",
        "report/common_templates.xml",
        "report/report_views.xml",
        "report/mod592_csv.xml",
        "data/ir_sequence_data.xml"
    ],
    "development_status": "Beta",
    "installable": True,
}
