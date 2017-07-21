# -*- coding: utf-8 -*-
# Copyright 2016 Comunitea Servicios Tecnológicos <omar@comunitea.com>
# Copyright 2017 Tecnativa - Luis M. Ontalba <luis.martinez@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Account Banking Sepa - FSDD (Anticipos de crédito)",
    "version": "10.0.1.0.0",
    "author": "Tecnativa, "
              "Odoo Community Association (OCA)",
    'license': 'AGPL-3',
    "website": "http://www.comunitea.com",
    "category": "Banking addons",
    "depends": [
        "account_banking_sepa_direct_debit",
    ],
    "data": [
        "views/payment_mode_view.xml",
    ],
    'installable': True,
}
