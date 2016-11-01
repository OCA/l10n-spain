# -*- coding: utf-8 -*-
# Copyright 2004-2011 Pexego Sistemas Informáticos
# Copyright 2013 Zikzakmedia
# Copyright 2014 Juanjo Algaz
# Copyright 2014 Joaquín Gutierrez <joaquing.pedrosa@gmail.com>
# Copyright 2014-2016 Tecnativa - Pedro M. Baeza
# Copyright 2016 Tecnativa - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl-3.0).

{
    "name": "Informes de cuentas anuales españoles",
    "version": "9.0.1.0.0",
    "author": "Pexego, "
              "Tecnativa,"
              "Zikzakmedia,"
              "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "http://www.pexego.es",
    "category": "Localisation/Accounting",
    "depends": [
        'l10n_es',
        'account_balance_reporting',
    ],
    "data": [
        'data/balance_pymes.xml',
        'data/pyg_pymes.xml',
        'data/balance_abreviado.xml',
        'data/pyg_abreviado.xml',
        'data/balance_normal.xml',
        'data/pyg_normal.xml',
        'data/estado_ingresos_gastos_normal.xml',
    ],
    'installable': True,
}
