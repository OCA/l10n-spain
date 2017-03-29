# -*- coding: utf-8 -*-
# Copyright 2008-2010 Jordi Esteve <jesteve@zikzakmedia.com>
# Copyright 2012-2013, Dpto. Consultoría <consultoria@opentia.es>
# Copyright 2013-2015 Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
# Copyright 2015 Carlos Liébana <carlos.liebana@factorlibre.com>
# Copyright 2015 Hugo Santos <hugo.santos@factorlibre.com>
# Copyright 2015 Albert Cabedo <albert@gafic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Spanish Charts of Accounts (PGCE 2008)",
    "version": "8.0.5.4.0",
    "author": "Spanish Localization Team,"
              # "Zikzakmedia S.L.,"
              # "Grupo Opentia,"
              # "Serv. Tecnol. Avanzados - Pedro M. Baeza,"
              # "FactorLibre,"
              # "GAFIC consultores,"
              "Odoo Community Association (OCA)",
    "website": 'https://github.com/OCA/l10n-spain',
    "category": "Localization/Account Charts",
    "license": "AGPL-3",
    "depends": ["account", "base_vat", "base_iban"],
    "data": [
        "data/account_type.xml",
        "data/account_chart_template.xml",
        "data/account_account_common.xml",
        "data/account_account_full.xml",
        "data/account_account_pymes.xml",
        "data/account_account_assoc.xml",
        "data/tax_codes_common.xml",
        "data/taxes_common.xml",
        "data/fiscal_positions_common.xml",
        "data/account_chart_template_post.xml",
        "data/l10n_es_wizard.xml",
    ],
    'test': [
        'test/tax.yml'
    ],
    "installable": True,
    'images': [
        'images/config_chart_l10n_es.png',
        'images/l10n_es_chart.png'
    ],
}
