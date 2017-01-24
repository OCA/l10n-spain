# -*- coding: utf-8 -*-
# © 2009 Jordi Esteve <jesteve@zikzakmedia.com>
# © 2013 Ignacio Ibeas <ignacio@acysos.com>
# © 2015 Sergio Teruel <sergio@incaser.es>
# © 2013-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Adaptación de los clientes, proveedores y bancos para España",
    "version": "9.0.1.0.1",
    "author": "ZikZak,"
              "Acysos,"
              "Tecnativa,"
              "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "category": "Localisation/Europe",
    "license": "AGPL-3",
    "external_dependencies": {
        'python': [
            'requests',
        ],
    },
    "depends": [
        "account",
        "base_iban",
        "base_vat",
        "l10n_es_toponyms",
    ],
    "data": [
        "data/l10n_es_partner_data.xml",
        "views/account_journal_view.xml",
        "views/res_bank_view.xml",
        "views/res_partner_view.xml",
        "views/res_partner_bank_view.xml",
        "wizard/l10n_es_partner_wizard.xml",
    ],
    'installable': True,
}
