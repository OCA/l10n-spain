# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Punto de venta adaptado a la legislación española",
    "category": "Sales/Point Of Sale",
    "author": "Tecnativa, "
    "Aselcis Consulting, "
    "Acysos S.L., "
    "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "version": "16.0.1.0.2",
    "depends": ["point_of_sale"],
    "data": ["views/pos_views.xml", "views/res_config_settings_views.xml"],
    "assets": {
        "point_of_sale.assets": [
            "l10n_es_pos/static/src/xml/pos.xml",
            "l10n_es_pos/static/src/xml/Screens/OrderManagementScreen/TicketScreen.xml",
            "l10n_es_pos/static/src/js/PaymentScreen.js",
            "l10n_es_pos/static/src/js/models.js",
            "l10n_es_pos/static/src/js/Screens/TicketScreen/TicketScreen.js",
        ],
    },
    "installable": True,
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
}
