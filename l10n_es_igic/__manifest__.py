# Copyright 2004-2011 Pexego Sistemas Informáticos.
# Copyright 2014 Arturo Esparragón Goncalves (https://sdatos.com).
# Copyright 2016-2018 Rodrigo Colombo Vlaeminch (https://sdatos.com).
# Copyright 2019-2023 Comunitea Servicios Tecnológicos (https://comunitea.com).
# Copyright 2019 Héctor J. Ravelo (http://sdatos.com)
# License AGPL-3 - See See https://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "IGIC (Impuesto General Indirecto Canario",
    "version": "16.0.1.4.0",
    "author": "David Diz Martínez,"
    "Atlantux Consultores - Enrique Zanardi,"
    "Sistemas de Datos,"
    "Comunitea,"
    "Odoo Community Association (OCA)",
    "category": "Accounting/Localizations/Account Charts",
    "website": "https://github.com/OCA/l10n-spain",
    "depends": ["l10n_es"],
    "license": "AGPL-3",
    "data": [
        "data/account_chart_template_data.xml",
        "data/account.account.template-common-canary.csv",
        "data/account.account.template-pymes-canary.csv",
        "data/account.account.template-assoc-canary.csv",
        "data/account.account.template-full-canary.csv",
        "data/account_tax_group_data.xml",
        "data/account_tax_data.xml",
        "data/account_fiscal_position_template_canary_data.xml",
    ],
    "installable": True,
    "auto_install": False,
}
