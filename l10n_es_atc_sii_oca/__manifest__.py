# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Suministro Inmediato de Información en el IGIC",
    "version": "16.0.1.0.0",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Sistemas de Datos S.L, "
    "Comunitea, "
    "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "development_status": "Mature",
    "depends": [
        "l10n_es_aeat_sii_oca",
        "l10n_es_atc",
        "l10n_es_igic",
    ],
    "data": [
        "data/aeat_sii_tax_agency_data.xml",
        "data/aeat_sii_mapping_registration_keys_data.xml",
        "data/aeat_sii_map_data.xml",
    ],
    "images": ["static/description/icon.png"],
}
