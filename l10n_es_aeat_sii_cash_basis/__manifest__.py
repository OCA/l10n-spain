# -*- coding: utf-8 -*-
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": u"SII - Extensión para criterio de caja",
    "version": "10.0.1.0.0",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Tecnativa,"
              "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "account_payment_partner",
        "account_tax_cash_basis",
        "l10n_es_aeat_sii",
    ],
    "maintainers": [
        'pedrobaeza',
    ],
    "data": [
        'security/ir.model.access.csv',
        'data/aeat_sii_payment_mode_key_data.xml',
        'views/account_invoice_views.xml',
        'views/account_payment_method_views.xml',
        'views/account_payment_mode_views.xml',
        'views/aeat_sii_payment_mode_key_view.xml',
    ],
}
