# -*- coding: utf-8 -*-
# Copyright 2004-2011 Luis Manuel Angueira Blanco - Pexego
# Copyright 2013 Ignacio Ibeas - Acysos S.L. (http://acysos.com)
# Copyright 2015 Ainara Galdona <agaldona@avanzosc.com>
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# Copyright 2013-2017 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

{
    'name': "AEAT Base",
    'summary': "Modulo base para declaraciones de la AEAT",
    'version': "11.0.1.0.1",
    'author': "Pexego,"
              "Acysos,"
              "AvanzOSC,"
              "Tecnativa,"
              "Odoo Community Association (OCA)",
    'license': "AGPL-3",
    'website': "https://odoo-community.org/",
    'category': "Accounting & Finance",
    'depends': [
        'account_invoicing',
        'base_iban',
        'account_tax_balance',
    ],
    'external_dependencies': {
        'python': ['unidecode'],
    },
    'data': [
        'security/aeat_security.xml',
        'security/ir.model.access.csv',
        'data/aeat_partner.xml',
        'wizard/export_to_boe_wizard.xml',
        'views/aeat_menuitem.xml',
        'views/aeat_report_view.xml',
        'views/aeat_tax_line_view.xml',
        'views/aeat_export_configuration_view.xml',
        'views/aeat_tax_code_mapping_view.xml',
        'views/account_move_line_view.xml',
    ],
    'installable': True,
}
