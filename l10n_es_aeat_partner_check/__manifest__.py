# Copyright 2019 Acysos S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'AEAT - Comprobación de Calidad de datos identificativos',
    'author': 'Acysos S.L.,'
              'Odoo Community Association (OCA)',
    'website': 'https://www.aeodoo.org',
    'category': 'Accounting',
    'version': '10.0.0.1.0',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'base_vat',
        'l10n_es_aeat_soap'
    ],
    'data': [
        'views/res_partner_view.xml',
        'views/res_company_view.xml'
    ],
    'installable': True,
}
