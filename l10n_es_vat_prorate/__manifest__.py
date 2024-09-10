# Copyright 2022 Creu Blanca
# Copyright 2023 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Prorrata de IVA",
    "summary": "Prorrata de IVA para la localización española",
    "version": "16.0.1.1.0",
    "license": "AGPL-3",
    "author": "Creu Blanca, Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "depends": ["l10n_es_aeat"],
    "data": [
        "security/ir.model.access.csv",
        "data/account_template_tax.xml",
        "views/account_move_views.xml",
        "views/account_tax_views.xml",
        "views/res_company_prorate_views.xml",
        "views/res_company_views.xml",
    ],
}
