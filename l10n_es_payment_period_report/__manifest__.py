# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Spanish supplier payment period report",
    "version": "15.0.1.0.0",
    "category": "Accounting",
    "summary": "Supplier payment period report for Spanish legal disclosure",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "maintainers": ["carlosdauden"],
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": ["account_financial_report"],
    "data": [
        "security/ir.model.access.csv",
        "wizards/payment_period_report_wizard_views.xml",
        "report/payment_period_report_pdf.xml",
        "report/payment_period_report_xlsx.xml",
    ],
    "development_status": "Alpha",
    "installable": True,
}
