# -*- coding: utf-8 -*-
# Copyright 2013 Alberto Martín Cortada (Guadaltech)
# Copyright 2015 AvanzOSC - Ainara Galdona
# Copyright 2016 Tecnativa - Antonio Espinosa <antonio.espinosa@tecnativa.com>
# Copyright 2014-2017 Tecnativa - Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

{
    "name": "AEAT modelo 303",
    "version": "10.0.1.3.0",
    'category': "Accounting & Finance",
    'author': "Guadaltech,"
              "AvanzOSC,"
              "Tecnativa,"
              "Odoo Community Association (OCA)",
    'website': "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": [
        "l10n_es",
        "l10n_es_aeat",
    ],
    "data": [
        "data/tax_code_map_mod303_data.xml",
        "data/aeat_export_mod303_data.xml",
        "data/aeat_export_mod303_2017_data.xml",
        "views/mod303_view.xml",
        "security/l10n_es_aeat_mod303_security.xml",
        "security/ir.model.access.csv",
    ],
    'installable': True,
}
