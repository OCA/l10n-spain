# -*- encoding: utf-8 -*-
#    Copyright 2018 Sistemas de Datos - Rodrigo Colombo Vlaeminch <rcolombo@sdatos.es>
#    License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

{
    'name' : 'ATC modelo 420',
    'version' : '10.0.1.0.0',
    'author' : 'Sistemas de Datos,'
               'Odoo Community Association (OCA)',
    'category' : 'Accounting',
    'website': 'https://github.com/OCA/l10n-spain',
    'license': "AGPL-3",
    'depends' : ['l10n_es_igic',
                 'l10n_es_aeat'],
    'data': ['data/tax_code_map_mod420_data.xml',
             'views/mod420_view.xml',
             'reports/mod420_report.xml',
             'security/ir.model.access.csv'],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
