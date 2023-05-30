# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Punto de venta adaptado a la legislación española por " "dispositivo",
    "category": "Sales/Point Of Sale",
    "author": "Landoo Sistemas de Información S.L, " "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "version": "14.0.1.1.1",
    "maintainers": ["ao-landoo"],
    "depends": ["l10n_es_pos"],
    "data": [
        "security/ir.model.access.csv",
        "security/device_security.xml",
        "views/pos_templates.xml",
        "views/pos_views.xml",
        "views/res_config_views.xml",
    ],
    "qweb": [
        "static/src/xml/Screens/Chrome/Chrome.xml",
        "static/src/xml/Screens/Chrome/DeviceName.xml",
    ],
    "installable": True,
}
