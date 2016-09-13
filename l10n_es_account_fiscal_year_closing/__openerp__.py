# -*- coding: utf-8 -*-
# Copyright 2008 Pedro Tarrafeta <pedro@acysos.com>
# Copyright 2009 Jordi Esteve <jesteve@zikzakmedia.com>
# Copyright 2012 Pedro Manuel Baeza <pedro.baeza@serviciosbaeza.com>
# Copyright 2012 Avanzosc (http://www.avanzosc.com)
# Copyright 2013 Joaquin Gutierrez (http://www.gutierrezweb.es)
# Copyright 2013 Pedro Manuel Baeza <pedro.baeza@serviciosbaeza.com>
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": u"Cierre de ejercicio fiscal para España",
    "summary": u"Configura el asistente para el cierre contable "
               u"según la contabilidad española",
    "version": "9.0.1.0.0",
    "category": "Localisation/Accounting",
    'website': "https://odoo-community.org/",
    "author": "Pexego, "
              "Tecnativa, "
              "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "l10n_es",
        "account_fiscal_year_closing",
    ],
}
