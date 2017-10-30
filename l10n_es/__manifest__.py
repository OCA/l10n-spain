# -*- coding: utf-8 -*-
# Copyright 2008-2010 Jordi Esteve - Zikzakmedia S.L.
# Copyright 2011 Ignacio - Ibeas - Acysos
# Copyright 2012-2013 Grupo Opentia
# Copyright 2014 Pablo Cayuela - Aserti Global Solutions
# Copyright 2014 Ángel Moya - Domatix
# Copyright 2015 Carlos Liébana - Factor Libre
# Copyright 2015 Albert Cabedo - GAFIC consultores
# Copyright 2013-2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Planes de cuentas españoles (según PGCE 2008)",
    "version": "10.0.2.1.0",
    "author": "Spanish Localization Team, "
              "Odoo Community Association (OCA)",
    "website": 'https://github.com/OCA/l10n-spain',
    "category": "Localization/Account Charts",
    "license": "AGPL-3",
    "depends": [
        "account",
        "base_vat",
        "base_iban",
    ],
    "data": [
        "data/account_type.xml",
        "data/account_chart_template.xml",
        "data/account_account_common.xml",
        "data/account_account_full.xml",
        "data/account_account_pymes.xml",
        "data/account_account_assoc.xml",
        "data/account_tax_group_data.xml",
        "data/taxes_common.xml",
        "data/fiscal_positions_common.xml",
        "data/account_chart_template_post.xml",
        "views/report_invoice.xml",
    ],
    'installable': True,
    'images': [
        'images/config_chart_l10n_es.png',
        'images/l10n_es_chart.png'
    ],
}
