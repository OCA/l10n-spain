# Copyright 2016 - FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# Copyright 2009-2017 Noviat.
# Copyright 2019 - FactorLibre - Daniel Duque <daniel.duque@factorlibre.com>
# Copyright 2020 - Tecnativa - Manuel Calero
# Copyright 2020 - Tecnativa - Pedro M. Baeza
# Copyright 2021 Tecnativa - João Marques
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Intrastat Product Declaration for Spain",
    "version": "15.0.1.0.0",
    "category": "Intrastat",
    "license": "AGPL-3",
    "summary": "Spanish Intrastat Product Declaration",
    "author": "FactorLibre,Noviat,Tecnativa,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "depends": ["intrastat_product", "l10n_es_aeat"],
    "conflicts": ["report_intrastat"],
    "data": [
        "security/l10n_es_intrastat_report_security.xml",
        "security/ir.model.access.csv",
        "data/intrastat_transaction.xml",
        "data/account_fiscal_position_template.xml",
        "views/l10n_es_intrastat_product.xml",
        "wizards/l10n_es_intrastat_code_import.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
}
