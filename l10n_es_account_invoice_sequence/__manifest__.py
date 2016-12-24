# -*- coding: utf-8 -*-
# Copyright 2011 NaN Projectes de Programari Lliure, S.L.
# Copyright 2014 Ángel Moya (Domatix)
# Copyright 2014 Roberto Lizana (Trey)
# Copyright 2013-2016 Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Secuencia para facturas separada de la secuencia de asientos",
    "version": "10.0.1.0.0",
    "author": "Spanish Localization Team, "
              "NaN·Tic, "
              "Trey, "
              "Tecnativa, "
              "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "category": "Accounting",
    "license": "AGPL-3",
    "depends": [
        'l10n_es',
    ],
    "data": [
        'data/sequence_data.xml',
        'views/account_journal_view.xml',
    ],
    "post_init_hook": "post_init_hook",
    'installable': True,
}
