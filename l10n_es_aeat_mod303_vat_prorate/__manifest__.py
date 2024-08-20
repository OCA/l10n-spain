# Copyright 2023 Tecnativa - Víctor Martínez
# Copyright 2023 Tecnativa - Pedro M. Baeza
# Copyright 2023 Tecnativa - Carolina Fernandez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Prorrata de IVA [303]",
    "version": "17.0.3.0.0",
    "category": "Accounting",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["l10n_es_vat_prorate", "l10n_es_aeat_mod303"],
    "data": [
        "data/2023/aeat.model.export.config.line.csv",
        "views/mod303_views.xml",
    ],
    "installable": True,
    "maintainers": ["victoralmau", "pedrobaeza"],
}
