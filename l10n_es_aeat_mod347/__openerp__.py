# -*- coding: utf-8 -*-
# © 2004-2011 Pexego Sistemas Informáticos. (http://pexego.es)
# © 2012 NaN·Tic  (http://www.nan-tic.com)
# © 2013 Acysos (http://www.acysos.com)
# © 2013 Joaquín Pedrosa Gutierrez (http://gutierrezweb.es)
# © 2014-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
#             (http://www.serviciosbaeza.com)
# © 2016 Antiun Ingenieria S.L. - Antonio Espinosa
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': "Modelo 347 AEAT",
    'version': "8.0.1.5.0",
    'author': "Pexego,"
              "ASR-OSS,"
              "NaN·tic,"
              "Acysos,"
              "Serv. Tecnol. Avanzados - Pedro M. Baeza,"
              "Antiun Ingeniería S.L.,"
              "Odoo Community Association (OCA)",
    'website': "https://github.com/OCA/l10n-spain",
    'contributors': [
        'Pexego (http://www.pexego.es)',
        'ASR-OSS (http://www.asr-oss.com)',
        'NaN·tic (http://www.nan-tic.com)',
        'Acysos (http://www.acysos.com)',
        'Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>',
        'Joaquín Gutierrez (http://gutierrezweb.es)',
        'Comunitea (http://www.comunitea.com)',
        'Antonio Espinosa <antonioea@antiun.com>',
    ],
    'category': "Localisation/Accounting",
    'license': "AGPL-3",
    'depends': [
        "base_vat",
        "l10n_es_aeat",
        "account_invoice_currency",
    ],
    'data': [
        "security/ir.model.access.csv",
        "security/mod_347_security.xml",
        "wizard/export_mod347_to_boe.xml",
        "views/account_period_view.xml",
        "views/account_invoice_view.xml",
        "views/res_partner_view.xml",
        "views/mod347_view.xml",
        "report/mod347_report.xml",
    ],
    'installable': True,
    "post_init_hook": "post_init_hook",
    'images': [
        'images/l10n_es_aeat_mod347.png',
    ],
}
