# © 2019 Solvos Consultoría Informática (<http://www.solvos.es>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "PVR y descuentos por tarifa en detalle de tique",
    "summary":
        "Muestra el PVR y el descuento según tarifas por línea de tique",
    "category": "Point Of Sale",
    "author": "Solvos, "
              "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "version": "12.0.1.0.0",
    "depends": [
        "l10n_es_pos",
    ],
    "data": [
        "views/pos_templates.xml",
    ],
    "qweb": [
        "static/src/xml/pos.xml",
    ],
    "installable": True,
}
