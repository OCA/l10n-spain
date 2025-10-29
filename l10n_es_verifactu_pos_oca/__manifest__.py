{
    "name": "Comunicación Veri*FACTU: TPV",
    "version": "14.0.1.0.0",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Factor Libre S.L., Binhex, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "l10n_es_pos",
        "l10n_es_verifactu_oca",
        "pos_default_partner",
    ],
    "qweb": [
        "static/src/xml/pos.xml",
    ],
    "data": [
        "views/pos_templates.xml",
        "views/pos_order_view.xml",
    ],
}
