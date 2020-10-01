# Copyright 2013 Alberto Martín Cortada (Guadaltech)
# Copyright 2015 AvanzOSC - Ainara Galdona
# Copyright 2016 Tecnativa - Antonio Espinosa
# Copyright 2017 ForgeFlow, S.L.
# Copyright 2014-2020 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

{
    "name": "AEAT modelo 303",
    "version": "13.0.1.2.0",
    "category": "Accounting",
    "author": "Guadaltech,"
    "AvanzOSC,"
    "Tecnativa,"
    "ForgeFlow,"
    "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": ["l10n_es", "l10n_es_aeat"],
    "data": [
        "data/tax_code_map_mod303_data.xml",
        "data/aeat_export_mod303_data.xml",
        "data/aeat_export_mod303_2017_data.xml",
        "data/aeat_export_mod303_2018_data.xml",
        "data/l10n_es_aeat_mod303_report_activity_code_data.xml",
        "views/mod303_view.xml",
        "views/l10n_es_aeat_mod303_report_activity_code_data_views.xml",
        "security/l10n_es_aeat_mod303_security.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
}
