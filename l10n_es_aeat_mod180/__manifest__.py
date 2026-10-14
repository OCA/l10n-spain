# Copyright 2025 Netkia Soluciones SLU - Carlos Sainz-Pardo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "AEAT Modelo 180",
    "summary": "AEAT Modelo 180",
    "author": "Netkia Soluciones SLU, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/l10n-spain",
    "version": "18.0.1.0.0",
    "depends": [
        "l10n_es_aeat",
        "l10n_es_aeat_mod115",
    ],
    "data": [
        "data/aeat_export_mod180_line_data.xml",
        "data/aeat_export_mod180_data.xml",
        "security/l10n_es_aeat_mod180_security.xml",
        "security/ir.model.access.csv",
        "views/mod180_view.xml",
        "views/recipient_record_views.xml",
    ],
    "installable": True,
    "maintainers": ["carlossainznetkia"],
}
