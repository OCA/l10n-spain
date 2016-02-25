# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C)
#        2004-2011:  Pexego Sistemas Informáticos. (http://pexego.es)
#        2012:       NaN·Tic  (http://www.nan-tic.com)
#        2013:       Acysos (http://www.acysos.com)
#                    Joaquín Pedrosa Gutierrez (http://gutierrezweb.es)
#        2014-2015:  Serv. Tecnol. Avanzados - Pedro M. Baeza
#                    (http://www.serviciosbaeza.com)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': "Modelo 347 AEAT",
    'version': "8.0.1.3.1",
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
