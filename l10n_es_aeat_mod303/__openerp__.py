# -*- coding: utf-8 -*-
# © 2013 Alberto Martín Cortada (Guadaltech)
# © 2014-2015 Pedro M. Baeza
# © 2015 AvanzOSC - Ainara Galdona
# © 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

{
    "name": "AEAT modelo 303",
    "version": "9.0.1.0.0",
    'category': "Accounting & Finance",
    'author': "Guadaltech,"
              "AvanzOSC,"
              "Serv. Tecnol. Avanzados - Pedro M. Baeza,"
              "Antiun Ingeniería S.L.,"
              "Comunitea,"
              "Odoo Community Association (OCA)",
    'website': "https://odoo-community.org/",
    "license": "AGPL-3",
    "depends": [
        "l10n_es",
        "l10n_es_aeat",
    ],
    "data": [
        "data/tax_code_map_mod303_data.xml",
        "data/aeat_export_mod303_data.xml",
        "views/mod303_view.xml",
        "security/ir.model.access.csv",
    ],
    'installable': True,
}
