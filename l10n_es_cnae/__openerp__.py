# -*- coding: utf-8 -*-
# Copyright 2016 Jairo Llopis <jairo.llopis@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Categorías de empresa CNAE 2009",
    "summary": "Extiende los códigos NACE europeos con los CNAE españoles",
    "version": "9.0.1.0.0",
    "category": "Localization",
    "website": "https://www.tecnativa.com/",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "l10n_eu_nace",
    ],
    "data": [
        "data/res.partner.category.csv",
    ],
}
