# Copyright 2024 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "L10n Es Payment Ratio",
    "summary": """
        Create a report to see your payment ratio""",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "Dixmit,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "depends": ["account", "report_xlsx"],
    "data": [
        "security/ir.model.access.csv",
        "wizards/company_payment_ratio_wizard.xml",
        "views/account_move.xml",
        "reports/reports.xml",
    ],
    "demo": [],
    "pre_init_hook": "pre_init_hook",
    "maintainers": ["pedrobaeza"],
}
