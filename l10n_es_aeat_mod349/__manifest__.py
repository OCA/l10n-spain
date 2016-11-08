# -*- coding: utf-8 -*-
# Copyright 2004-2011 - Pexego Sistemas Informáticos. (http://pexego.es)
# Copyright 2013 - Top Consultant Software Creations S.L.
#                - (http://www.topconsultant.es/)
# Copyright 2014-2015 - Serv. Tecnol. Avanzados
#                     - Pedro M. Baeza (http://www.serviciosbaeza.com)
# Copyright 2016 - Tecnativa - Angel Moya <odoo@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
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
    "version": "9.0.1.0.0",
    "author": "Pexego, "
              "Top Consultant, "
              "Serv. Tecnol. Avanzados - Pedro M. Baeza, "
              "Antiun Ingeniería S.L.,"
              "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "category": 'Localisation/Accounting',
    'website': 'https://github.com/OCA/l10n-spain',
    "depends": [
        "account_refund_original",
        "l10n_es_aeat",
    ],
    'data': [
        "data/aeat_export_mod349_partner_refund_data.xml",
        "data/aeat_export_mod349_partner_data.xml",
        "data/aeat_export_mod349_data.xml",
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
