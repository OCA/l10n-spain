# © 2017 FactorLibre - Hugo Santos <hugo.santos@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Envio de factura simplificada resumen TPV a SII',
    'version': '8.0.1.0.0',
    'depends': [
        'point_of_sale',
        'l10n_es_aeat_sii'
    ],
    'category': "Accounting & Finance",
    'author': 'FactorLibre',
    'license': 'AGPL-3',
    'website': 'http://www.factorlibre.com',
    'data': [
        'views/account_invoice_view.xml'
    ],
    'installable': True,
    'application': False
}
