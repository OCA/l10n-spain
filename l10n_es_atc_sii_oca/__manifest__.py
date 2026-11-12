# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Suministro Inmediato de Información en el IGIC",
    "version": "20.0.1.0.0",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Sistemas de Datos S.L, "
    "Comunitea, "
    "Tecnativa, "
    "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["carlosdauden"],
    "depends": [
        "l10n_es",
        "l10n_es_aeat_sii_oca",
        "l10n_es_atc",
    ],
    "data": [
        "security/ir.access.csv",
        "data/aeat_sii_tax_agency_data.xml",
        "views/account_move_views.xml",
        "views/account_tax_views.xml",
    ],
    "images": ["static/description/icon.png"],
    "post_init_hook": "post_init_hook",
}
