{
    "name": "Comunicación Veri*FACTU: TPV",
    "version": "18.0.1.0.0",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Factor Libre S.L., Alia Technologies, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "l10n_es_pos_oca",
        "l10n_es_verifactu_oca"
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "l10n_es_verifactu_pos_oca/static/src/**/*",
        ],
    },
    "data": [
        "views/pos_order_view.xml",
    ],
}
