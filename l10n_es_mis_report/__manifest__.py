# Copyright 2018 ForgeFlow, S.L. <contact@forgeflow.com>
# Copyright 2018-2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

{
    "name": "Plantillas MIS Builder para informes contables españoles",
    "summary": "Plantillas MIS Builder para informes contables españoles",
    "author": "ForgeFlow, Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "category": "Reporting",
    "version": "15.0.1.0.1",
    "license": "AGPL-3",
    "depends": ["l10n_es", "mis_builder"],  # OCA/mis-builder
    "data": [
        "data/mis_report_styles.xml",
        "data/mis_report_balance_abreviated.xml",
        "data/mis_report_balance_normal.xml",
        "data/mis_report_balance_sme.xml",
        "data/mis_report_balance_sme_sfl.xml",
        "data/mis_report_pyg_abreviated.xml",
        "data/mis_report_pyg_normal.xml",
        "data/mis_report_pyg_sme.xml",
        "data/mis_report_pyg_sme_sfl.xml",
        "data/mis_report_revenues_expenses_normal.xml",
    ],
    "installable": True,
}
