# © 2020 FactorLibre - Rodrigo Bonilla <rodrigo.bonilla@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Envio de factura simplificada resumen a SII',
    'version': '11.0.1.0.0',
    'depends': [
        'l10n_es_aeat_sii',
    ],
    'category': "Accounting & Finance",
    'author': "FactorLibre,"
                "Odoo Community Association (OCA)",
    'license': 'AGPL-3',
    'website': 'http://www.factorlibre.com',
    'data': [
        'views/account_invoice_view.xml'
    ],
    'installable': True,
    'application': False
}
