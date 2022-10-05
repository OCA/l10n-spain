# Copyright 2014-2019 Tecnativa - Pedro M. Baeza

{
    "name": "AEAT modelo 130",
    "version": "12.0.1.3.1",
    "author": "Tecnativa, "
              "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    'website': "https://github.com/OCA/l10n-spain",
    "category": "Localization/Accounting",
    "depends": [
        "l10n_es_aeat",
    ],
    "data": [
        "data/aeat_export_mod130_data.xml",
        "views/mod130_view.xml",
        "security/ir.model.access.csv",
        "security/ir_rule.xml"
    ],
    "installable": True,
}
