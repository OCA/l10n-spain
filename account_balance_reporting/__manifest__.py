# Copyright 2009 Pexego/Comunitea
# Copyright 2011-2012 Iker Coranti (www.avanzosc.es)
# Copyright 2014 Juanjo Algaz (gutierrezweb.es)
# Copyright 2014-2017 Tecnativa - Pedro M. Baeza
# Copyright 2016 Tecnativa - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl-3.0).

{
    "name": "Account balance reporting engine",
    "version": "11.0.1.0.0",
    "author": "Pexego, "
              "AvanzOSC, "
              "Tecnativa, "
              "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "category": "Accounting & Finance",
    "license": 'AGPL-3',
    "depends": [
        "account",
        "date_range",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/account_balance_reporting_template_view.xml",
        "views/account_balance_reporting_report_view.xml",
        "views/account_balance_reporting_menu.xml",
        "report/account_balance_reporting_reports.xml",
        "report/report_generic.xml",
        "wizard/wizard_print_view.xml",
    ],
    'installable': True,
}
