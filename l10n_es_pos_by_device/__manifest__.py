# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Punto de venta adaptado a la legislación española por dispositivo",
    "summary": "Múltiples dispositivos por sesión en el punto de venta",
    "category": "Sales/Point Of Sale",
    "author": "Landoo Sistemas de Información S.L, " "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "version": "16.0.1.0.1",
    "maintainers": ["ao-landoo"],
    "depends": ["l10n_es_pos"],
    "data": [
        "security/ir.model.access.csv",
        "security/device_security.xml",
        "views/pos_views.xml",
        "views/res_config_views.xml",
    ],
    "assets": {
        "point_of_sale.assets": [
            "l10n_es_pos_by_device/static/src/xml/**/*",
            "l10n_es_pos_by_device/static/src/js/**/*",
        ],
    },
    "installable": True,
}
