# -*- coding: utf-8 -*-
# Copyright 2016 Tecnativa - Antonio Espinosa
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": u"Cierre de ejercicio fiscal para España",
    "summary": u"Configuraciones para el asistente de cierre contable según "
               u"la contabilidad española",
    "version": "9.0.1.0.0",
    "category": "Localisation/Accounting",
    'website': "https://odoospain.odoo.com",
    "author": "Tecnativa, "
              "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "l10n_es",
        "account_fiscal_year_closing",
    ],
    "data": [
        "data/l10n_es_account_fiscal_year_closing_data.xml",
    ],
}
