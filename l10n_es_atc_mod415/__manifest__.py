# Copyright 2014-2023 Binhex - Nicolás Ramos (http://binhex.es)
# Copyright 2024 Binhex - Christian Ramos (http://binhex.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Basado en el modelo 347 de la AEAT
{
    "name": "ATC Modelo 415",
    "version": "17.0.1.0.0",
    "author": "Binhex System Solutions," "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "category": "Accounting",
    "license": "AGPL-3",
    "depends": [
        "l10n_es_aeat_mod347",
        "l10n_es_atc",
        "l10n_es_igic",
    ],
    "data": [
        "data/l10n.es.aeat.map.tax.line.tax.csv",
        "data/l10n.es.aeat.map.tax.csv",
        "data/l10n.es.aeat.map.tax.line.csv",
        "security/ir.model.access.csv",
        "security/mod_415_security.xml",
        "views/account_move_view.xml",
        "views/res_partner_view.xml",
        "views/mod415_view.xml",
        "views/report_415_partner.xml",
        "views/mod415_templates.xml",
        "data/mail_template_data.xml",
    ],
    "maintainers": ["Christian-RB"],
    "installable": True,
}
