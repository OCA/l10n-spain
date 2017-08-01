# -*- coding: utf-8 -*-
# © 2016 - FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Intrastat Product Declaration for Spain',
    'version': '8.0.1.0.0',
    'category': 'Intrastat',
    'license': 'AGPL-3',
    'summary': 'Spanish Intrastat Product Declaration',
    'author': 'FactorLibre, Noviat, Odoo Community Association (OCA)',
    'depends': [
        'intrastat_product',
        'l10n_es_aeat_mod349',
    ],
    'conflicts': [
        'l10n_es_intrastat',
        'report_intrastat',
    ],
    'data': [
        'security/intrastat_security.xml',
        'security/ir.model.access.csv',
        'data/intrastat_transaction.xml',
        'views/account_invoice.xml',
        'views/res_company.xml',
        # 'views/intrastat_installer.xml',
        'views/l10n_es_intrastat_product.xml',
    ],
    'installable': True,
}
