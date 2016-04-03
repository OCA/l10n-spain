# -*- coding: utf-8 -*-
# © 2009 Jordi Esteve <jesteve@zikzakmedia.com>
# © 2013 Ignacio Ibeas <ignacio@acysos.com>
# © 2015 Sergio Teruel <sergio@incaser.es>
# © 2013-2016 Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Adaptación de los clientes, proveedores y bancos para España",
    "version": "8.0.1.5.0",
    "author": "Spanish localization team,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "category": "Localisation/Europe",
    "license": "AGPL-3",
    "depends": [
        "base",
        "base_iban",
        "base_vat",
        "l10n_es_toponyms",
    ],
    "data": [
        "views/l10n_es_partner_view.xml",
        "wizard/l10n_es_partner_wizard.xml",
    ],
    "installable": True,
}
