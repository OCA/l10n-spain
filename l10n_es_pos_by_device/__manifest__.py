# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Punto de venta adaptado a la legislación española por dispositivo",
    "category": "Sales/Point Of Sale",
    "author": "Landoo Sistemas de Información S.L, " "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "version": "15.0.1.0.0",
    "maintainers": ["ao-landoo"],
    "depends": ["l10n_es_pos"],
    "data": [
        "security/ir.model.access.csv",
        "security/device_security.xml",
        "views/pos_views.xml",
        "views/res_config_views.xml",
    ],
    "assets": {
        "web.assets_qweb": [
            "l10n_es_pos_by_device/static/src/xml/Screens/Chrome/Chrome.xml",
            "l10n_es_pos_by_device/static/src/xml/Screens/Chrome/DeviceName.xml",
        ],
        "point_of_sale.assets": [
            "l10n_es_pos_by_device/static/src/js/models.js",
            "l10n_es_pos_by_device/static/src/js/PaymentScreen.js",
            "l10n_es_pos_by_device/static/src/js/Screens/Chrome/Chrome.js",
            "l10n_es_pos_by_device/static/src/js/Screens/Chrome/DeviceName.js",
            "l10n_es_pos_by_device/static/src/js/Screens/Popups/CashOpeningPopup.js",
            "l10n_es_pos_by_device/static/src/js/Screens/Popups/ClosePosPopup.js",
        ],
    },
    "installable": True,
}
