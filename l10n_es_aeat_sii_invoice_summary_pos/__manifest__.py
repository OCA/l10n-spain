# Copyright 2025 Binhex <https://www.binhex.cloud>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Rellenar campos de factura simplificada resumen TPV a SII",
    "summary": """
        Rellenar automáticamente los campos primera y última factura de
        resúmenes simplificados TPV a SII.
    """,
    "version": "17.0.1.0.0",
    "depends": [
        "l10n_es_aeat_sii_invoice_summary",
        "point_of_sale",
    ],
    "category": "Accounting & Finance",
    "author": "Binhex, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/l10n-spain",
    "data": ["data/res_partner_data.xml", "views/account_move_view.xml"],
    "installable": True,
    "application": False,
}
