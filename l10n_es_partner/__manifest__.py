# Copyright 2009 Jordi Esteve <jesteve@zikzakmedia.com>
# Copyright 2013 Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2015 Tecnativa - Sergio Teruel
# Copyright 2016 Tecnativa - Carlos Dauden
# Copyright 2013-2022 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Adaptación de los clientes, proveedores y bancos para España",
    "version": "17.0.1.0.5",
    "author": "ZikZak," "Acysos," "Tecnativa," "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "category": "Localisation/Europe",
    "license": "AGPL-3",
    "development_status": "Mature",
    "maintainers": ["pedrobaeza"],
    "depends": ["account", "base_bank_from_iban", "base_vat"],
    "data": [
        "data/l10n_es_partner_data.xml",
        "views/res_bank_view.xml",
        "views/res_partner_view.xml",
        "wizard/l10n_es_partner_wizard.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
}
