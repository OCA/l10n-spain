# Copyright 2009 Jordi Esteve <jesteve@zikzakmedia.com>
# Copyright 2013 Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2015 Tecnativa - Sergio Teruel
# Copyright 2016 Tecnativa - Carlos Dauden
# Copyright 2013-2017 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Adaptación de los clientes, proveedores y bancos para España",
    "version": "11.0.1.0.0",
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
    ],
    "data": [
        "data/l10n_es_partner_data.xml",
        "views/account_journal_view.xml",
        "views/res_bank_view.xml",
        "views/res_partner_view.xml",
        "wizard/l10n_es_partner_wizard.xml",
    ],
    'installable': True,
}
