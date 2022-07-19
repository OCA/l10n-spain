# Copyright (C) 2022 Trey, Kilobytes de Soluciones - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Asientos de apertura y cierre",
    "summary": "Crea los asientos de apertura y cierre a partir del balance de"
               " sumas y saldos.",
    "author": "Trey (www.trey.es), Odoo Community Association (OCA)",
    "maintainers": [
        "cubells",
    ],
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "category": "Accounting & Finance",
    "version": "12.0.1.0.0",
    "depends": [
        "account_financial_report",
        "report_xlsx",
        "l10n_es",
    ],
    "data": [
        "wizards/trial_balance_report_wizard_views.xml",
        "reports/opening_closing_report_views.xml",
    ],
}
