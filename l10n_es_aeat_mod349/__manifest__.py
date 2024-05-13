# Copyright 2004-2011 - Pexego Sistemas Informáticos. (http://pexego.es)
# Copyright 2013 - Top Consultant (http://www.topconsultant.es/)
# Copyright 2016 - Tecnativa - Angel Moya <odoo@tecnativa.com>
# Copyright 2017 - Tecnativa - Luis M. Ontalba <luis.martinez@tecnativa.com>
# Copyright 2017 ForgeFlow <contact@forgeflow.com>
# Copyright 2018 Tecnativa - Carlos Dauden
# Copyright 2014-2023 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "AEAT modelo 349",
    "version": "16.0.1.3.1",
    "author": "Tecnativa, ForgeFlow, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "category": "Localisation/Accounting",
    "website": "https://github.com/OCA/l10n-spain",
    "depends": ["l10n_es_aeat", "l10n_es"],
    "data": [
        "data/aeat_349_map_data.xml",
        "data/aeat_export_mod349_partner_refund_data.xml",
        "data/aeat_export_mod349_partner_data.xml",
        "data/aeat_export_mod349_data.xml",
        "views/account_move_view.xml",
        "views/account_tax_view.xml",
        "views/aeat_349_map_view.xml",
        "views/mod349_view.xml",
        "report/common_templates.xml",
        "report/aeat_mod349.xml",
        "report/report_views.xml",
        "security/ir.model.access.csv",
        "security/mod_349_security.xml",
    ],
    "development_status": "Mature",
    "maintainers": ["pedrobaeza"],
    "installable": True,
}
