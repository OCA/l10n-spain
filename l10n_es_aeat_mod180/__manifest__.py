# Copyright 2022 Netkia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
{
    "name": "AEAT Modelo 180",
    "summary": "AEAT Modelo 180",
    "author": "Netkia Soluciones SLU, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/l10n-spain",
    "version": "16.0.1.0.0",
    "depends": [
        "l10n_es_aeat_mod115",
    ],
    "data": [
        "data/aeat_export_mod180_line_data.xml",
        "data/aeat_export_mod180_data.xml",
        "security/ir.model.access.csv",
        "security/l10n_es_aeat_mod180_security.xml",
        "views/res_partner_views.xml",
        "views/mod180_view.xml",
        "views/account_move_views.xml",
        "views/account_move_line_views.xml",
        "views/recipient_record_views.xml",
        "views/l10n_es_aeat_real_estate_view.xml",
    ],
    "installable": True,
}
