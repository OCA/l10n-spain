# Copyright 2019 Acysos S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'AEAT Certificados',
    'author': 'Acysos S.L.,'
              'Odoo Community Association (OCA)',
    'website': 'https://www.aeodoo.org',
    'category': 'Accounting',
    'version': '10.0.0.1.0',
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
