# Copyright 2025 Juan Carlos Oñate - Tecnativa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Digital canon report",
    "summary": "Generate XLSX reports for digital canon operations",
    "version": "18.0.1.0.0",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "report_xlsx_helper",
        "l10n_es_digital_canon",
        "product_brand",
        "stock",
        "purchase",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizards/digital_canon_report_wizard.xml",
    ],
    "installable": True,
}
