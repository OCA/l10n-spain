# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Average Period of Payment to Suppliers (PMP) Spain",
    "version": "19.0.1.0.0",
    "category": "Accounting/Localizations/Reporting",
    "summary": "Calculates the PMP according to ICAC 2016 Resolution and Law 18/2022",
    "author": "Acysos S.L., Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/pmp_wizard_views.xml",
    ],
    "installable": True,
    "application": False,
    "license": "AGPL-3",
}
