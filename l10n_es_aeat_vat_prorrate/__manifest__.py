# Copyright 2015 AvanzOSC - Ainara Galdona
# Copyright 2015-2020 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

{
    "name": "AEAT - Prorrata de IVA",
    "version": "13.0.1.0.0",
    "license": "AGPL-3",
    "author": "AvanzOSC, " "Tecnativa, " "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "category": "Invoices & Payments",
    "depends": ["l10n_es_aeat_mod303"],
    "data": [
        "data/tax_code_map_mod303_data.xml",
        "data/aeat_export_mod303_data.xml",
        "wizard/l10n_es_aeat_compute_vat_prorrate_view.xml",
        "views/mod303_view.xml",
    ],
    "installable": True,
}
