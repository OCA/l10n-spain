# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C)
#        2004-2011: Pexego Sistemas Informáticos. (http://pexego.es)
#        2013:      Top Consultant Software Creations S.L.
#                   (http://www.topconsultant.es/)
#        2014-2015: Serv. Tecnol. Avanzados - Pedro M. Baeza
#                   (http://www.serviciosbaeza.com)
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
    "name": "Modelo 349 AEAT",
    "version": "8.0.2.0.0",
    "author": "Pexego, "
              "Top Consultant, "
              "Serv. Tecnol. Avanzados - Pedro M. Baeza, "
              "Antiun Ingeniería S.L.,"
              "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "category": 'Localisation/Accounting',
    'website': 'https://github.com/OCA/l10n-spain',
    "depends": [
        "account",
        "account_invoice_currency",
        "account_refund_original",
        "l10n_es",
        "l10n_es_aeat",
    ],
    'data': [
        "wizard/export_mod349_to_boe.xml",
        "views/account_fiscal_position_view.xml",
        "views/account_invoice_view.xml",
        "views/mod349_view.xml",
        "report/mod349_report.xml",
        "security/ir.model.access.csv",
        "security/mod_349_security.xml",
    ],
    'post_init_hook': '_assign_invoice_operation_keys',
    'installable': True,
}
