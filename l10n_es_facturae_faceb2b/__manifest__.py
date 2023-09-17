# Copyright 2023 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "L10n Es Facturae Faceb2b",
    "summary": """
        Allow to send Facturae to customers using FaceB2B""",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "Dixmit,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "depends": ["l10n_es_facturae_face"],
    "data": [
        "security/ir.model.access.csv",
        "wizards/l10n_es_facturae_faceb2b_cancel.xml",
        "views/account_journal.xml",
        "data/edi.xml",
        "data/faceb2b_data.xml",
        "views/res_partner_view.xml",
        "views/account_move.xml",
        "views/report_facturae.xml",
    ],
    "demo": [],
}
