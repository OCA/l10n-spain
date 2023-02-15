# Copyright 2019 Acysos S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "AEAT - Comprobación de Calidad de datos identificativos",
    "author": "Acysos S.L., Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "category": "Accounting",
    "version": "16.0.1.0.1",
    "license": "AGPL-3",
    "depends": ["base", "base_vat", "l10n_es_aeat"],
    "data": [
        "views/res_partner_view.xml",
        "views/res_company_view.xml",
        "views/res_config_settings_view.xml",
    ],
    "installable": True,
}
