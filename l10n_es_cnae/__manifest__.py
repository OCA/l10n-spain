# Copyright 2016 Jairo Llopis <jairo.llopis@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Categorías de empresa CNAE 2025",
    "summary": "Extiende los códigos NACE europeos con los CNAE españoles",
    "version": "18.0.2.0.0",
    "category": "Localization",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Tecnativa, Moduon, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "post_init_hook": "post_init_hook",
    "depends": [
        "l10n_eu_nace",
    ],
}
