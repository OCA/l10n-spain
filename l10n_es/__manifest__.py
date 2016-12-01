# -*- coding: utf-8 -*-
# © 2008-2010 Jordi Esteve - Zikzakmedia S.L.
# © 2011 Ignacio - Ibeas - Acysos
# © 2012-2013 Grupo Opentia
# © 2014 Pablo Cayuela - Aserti Global Solutions
# © 2014 Ángel Moya - Domatix
# © 2015 Carlos Liébana - Factor Libre
# © 2015 Albert Cabedo - GAFIC consultores
# © 2013-2016 Serv. Tecnol. Avanzados - Pedro M. Baeza
# © 2013-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Planes de cuentas españoles (según PGCE 2008)",
    "version": "10.0.1.0.0",
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
        "data/taxes_common.xml",
        "data/fiscal_positions_common.xml",
        "data/account_chart_template_post.xml",
    ],
    'installable': True,
    'images': [
        'images/config_chart_l10n_es.png',
        'images/l10n_es_chart.png'
    ],
}
