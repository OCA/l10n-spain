# -*- coding: utf-8 -*-
# © 2009 Pexego/Comunitea
# © 2011-2012 Iker Coranti (www.avanzosc.es)
# © 2014 Juanjo Algaz (gutierrezweb.es)
# © 2014-2016 Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl-3.0).

{
    "name": "Account balance reporting engine",
    "version": "8.0.1.2.0",
    "author": "Pexego, "
              "AvanzOSC, "
              "Tecnativa, "
              "Odoo Community Association (OCA)",
    "website": "http://www.pexego.es",
    "category": "Accounting & Finance",
    "contributors": [
        "Juanjo Algaz <juanjoa@malagatic.com>",
        "Joaquín Gutierrez <joaquing.pedrosa@gmail.com>",
        "Pedro M. Baeza <pedro.baeza@tecnativa.com>",
        "Oihane Crucelaegui <oihanecrucelaegi@avanzosc.es>",
    ],
    "license": 'AGPL-3',
    "depends": [
        "account",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/account_account_view.xml",
        "views/account_balance_reporting_template_view.xml",
        "views/account_balance_reporting_report_view.xml",
        "views/account_balance_reporting_menu.xml",
        "report/account_balance_reporting_reports.xml",
        "report/report_generic.xml",
        "wizard/wizard_print_view.xml",
    ],
    'installable': False,
}
