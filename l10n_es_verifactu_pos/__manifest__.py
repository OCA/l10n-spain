{
    "name": "Comunicación Veri*FACTU: TPV",
    "version": "16.0.1.0.0",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Factor Libre S.L., Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "point_of_sale",
        "l10n_es_pos",
        "l10n_es_verifactu",
        "pos_default_partner",
    ],
    "assets": {
        "point_of_sale.assets": [
            "l10n_es_verifactu_pos/static/src/js/models.js",
            "l10n_es_verifactu_pos/static/src/xml/OrderReceipt.xml",
            "l10n_es_verifactu_pos/static/src/css/pos_receipts.css",
        ],
    },
    "data": [
        "views/pos_order_view.xml",
    ],
}
