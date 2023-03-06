# -*- coding: utf-8 -*-
# Copyright 2004-2011 Luis Manuel Angueira Blanco - Pexego
# Copyright 2013 Ignacio Ibeas - Acysos S.L. (http://acysos.com)
# Copyright 2015 Ainara Galdona <agaldona@avanzosc.com>
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# Copyright 2013-2018 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2018 Juan Vicente Pascual <jvpascual@puntsistemes.es>
# Copyright 2019 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

{
    'name': "AEAT Base",
    'summary': "Modulo base para declaraciones de la AEAT",
    'version': "11.0.3.1.0",
    'author': "Pexego,"
              "Acysos,"
              "AvanzOSC,"
              "Tecnativa,"
              "Odoo Community Association (OCA)",
    'license': "AGPL-3",
    "website": "https://github.com/OCA/l10n-spain",
    'category': "Accounting & Finance",
    'depends': [
        'account_invoicing',
        'base_iban',
        'account_tax_balance',
        'l10n_es',
    ],
    'external_dependencies': {
        'python': ['unidecode'],
    },
    'data': [
        'security/aeat_security.xml',
        'security/ir.model.access.csv',
        'data/aeat_partner.xml',
        'wizard/export_to_boe_wizard.xml',
        'wizard/compare_boe_file_views.xml',
        'views/aeat_menuitem.xml',
        'views/aeat_report_view.xml',
        'views/aeat_tax_line_view.xml',
        'views/aeat_export_configuration_view.xml',
        'views/aeat_tax_code_mapping_view.xml',
        'views/account_move_line_view.xml',
        'views/report_template.xml',
        'views/res_partner_view.xml',
    ],
    'installable': True,
}
