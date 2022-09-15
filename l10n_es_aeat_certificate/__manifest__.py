# Copyright 2019 Acysos S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'AEAT Certificados',
    'author': 'Diagram Software S.L.,'
              'Consultoría Informática Studio 73 S.L.,'
              'Acysos S.L.,'
              'Odoo Community Association (OCA)',
    "website": "https://github.com/OCA/l10n-spain",
    'category': 'Accounting',
    'version': '11.0.1.0.1',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'l10n_es_aeat'
    ],
    'data': [
        'views/aeat_certificate_view.xml',
        'wizards/aeat_certificate_password_view.xml',
        'security/aeat_certificate_security.xml',
        'security/ir.model.access.csv'
    ],
    'installable': True,
}
