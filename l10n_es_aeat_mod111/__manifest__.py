# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# Copyright 2017-2024 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl

{
    "name": "AEAT modelo 111",
    "version": "17.0.1.0.0",
    "development_status": "Mature",
    "category": "Localization/Accounting",
    "author": "AvanzOSC, "
    "RGB Consulting SL, "
    "Tecnativa, "
    "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": ["l10n_es_aeat"],
    "data": [
        "data/aeat_export_mod111_data.xml",
        "data/l10n.es.aeat.map.tax.csv",
        "data/l10n.es.aeat.map.tax.line.tax.csv",  # This one should be before the next
        "data/l10n.es.aeat.map.tax.line.csv",
        "views/mod111_view.xml",
        "security/ir.model.access.csv",
        "security/l10n_es_aeat_mod111_security.xml",
    ],
    "installable": True,
}
