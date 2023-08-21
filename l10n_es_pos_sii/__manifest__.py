# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Envío de pedidos del TPV al SII",
    "category": "Sales/Point Of Sale",
    "author": "Aures Tic, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "version": "15.0.1.0.1",
    "depends": [
        "point_of_sale",
        "l10n_es_pos",
        "l10n_es_aeat_sii_oca",
        "pos_default_partner",
    ],
    "data": [
        "views/pos_order.xml",
        "views/res_company.xml",
    ],
    "installable": True,
}
