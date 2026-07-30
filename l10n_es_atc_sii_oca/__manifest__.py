# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Suministro Inmediato de Información en el IGIC",
    "version": "18.0.1.0.3",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Sistemas de Datos S.L, "
    "Comunitea, "
    "Tecnativa, "
    "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "development_status": "Beta",
    "depends": [
        "l10n_es",
        "l10n_es_aeat_sii_oca",
        "l10n_es_atc",
    ],
    "data": [
        "data/aeat_sii_tax_agency_data.xml",
        "data/aeat_sii_mapping_registration_keys_data.xml",
        "data/l10n.es.aeat.map.tax.line.tax.csv",
        "data/atc_sii_map_data.xml",
        "views/product_template_views.xml",
        "views/account_fiscal_position_views.xml",
        "views/account_move_views.xml",
    ],
    "images": ["static/description/icon.png"],
}
