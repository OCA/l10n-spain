# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Envío de pedidos del TPV al SII",
    "category": "Sales/Point Of Sale",
    "author": "Aures Tic,Tecnativa,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "version": "18.0.1.0.5",
    "depends": [
        "point_of_sale",
        "l10n_es_pos_oca",
        "l10n_es_aeat_sii_oca",
    ],
    "data": [
        "data/ir_cron.xml",
        "views/pos_order.xml",
        "views/res_company.xml",
    ],
    "installable": True,
    "auto_install": True,
}
