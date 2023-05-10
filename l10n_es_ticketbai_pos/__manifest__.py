# Copyright 2021 Binovo IT Human Project SL
# Copyright 2022 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "TicketBAI - Point of Sale - "
    "declaración de todas las operaciones de venta realizadas por las personas "
    "y entidades que desarrollan actividades económicas",
    "version": "15.0.1.0.1",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Binovo," "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "auto_install": False,
    "development_status": "Beta",
    "maintainers": ["ao-landoo"],
    "depends": ["l10n_es_pos", "l10n_es_ticketbai"],
    "data": [
        "security/ir.model.access.csv",
        "views/l10n_es_ticketbai_pos_views.xml",
        "views/pos_order_views.xml",
        "views/ticketbai_certificate_views.xml",
    ],
    "assets": {
        "web.assets_qweb": [
            "l10n_es_ticketbai_pos/static/src/xml/pos.xml",
        ],
        "point_of_sale.assets": [
            "l10n_es_ticketbai_pos/static/lib/qrcode.js",
            "l10n_es_ticketbai_pos/static/lib/tbai.js",
            "l10n_es_ticketbai_pos/static/src/js/models.js",
            "l10n_es_ticketbai_pos/static/src/js/tbai_models.js",
            "l10n_es_ticketbai_pos/static/src/js/db.js",
            "l10n_es_ticketbai_pos/static/src/js/Screens/ClientListScreen/ClientListScreen.js",
            "l10n_es_ticketbai_pos/static/src/js/Screens/PaymentScreen/PaymentScreen.js",
            "l10n_es_ticketbai_pos/static/src/js/Screens/ProductScreen/ProductScreen.js",
        ],
    },
}
