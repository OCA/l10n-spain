# Copyright 2023 Moduon Team S.L. <info@moduon.team>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Actualizacion clave de registro SII",
    "summary": "Al cambiar la posición fiscal se cambia la clave de registro de SII ",
    "version": "14.0.1.0.0",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Moduon, Odoo Community Association (OCA)",
    "maintainers": ["shide", "anddago78"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "sale",
        "l10n_es_aeat_sii_oca",
    ],
    "auto_install": True,
}
