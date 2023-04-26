# (c) 2020 Comunitea Servicios Tecnológicos. Santi Argüeso"
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Exportación de fichero bancario Confirming para Abanca',
    'version': '11.0.1.0.0',
    'author': 'Comunitea, '
              'Odoo Community Association (OCA)',
    'contributors': [
        'Ramón castro ',
        'Santi Argüeso <santi@comunitea.com>'
        
    ],
    'category': 'Localisation/Accounting',
    'license': 'AGPL-3',
    'depends': [
        'l10n_es_base_confirming',
    ],
    'data': [
        'data/account_payment_method.xml',
        'views/account_payment_mode.xml',
    ],
    'installable': True,
}

