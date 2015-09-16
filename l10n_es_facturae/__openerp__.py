# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Alejandro Sanchez (http://www.asr-oss.com)
#                       Alejandro Sanchez <alejandro@asr-oss.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the Affero GNU General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the Affero GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name": "Creación de Factura-e (FACe)",
    "version": "1.0",
    "author": "ASR-OSS, "
              "FactorLibre, "
              "Tecon, "
              "Pexego, "
              "Malagatic, "
              "Comunitea, "
              "Odoo Community Association (OCA)",
    "category": "Localisation/Accounting",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": ["base", "account", "account_payment"],
    "data": [
        "country_view.xml",
        "data/data_res_country.xml",
        "partner_view.xml",
        "res_company.xml",
        "payment_mode_view.xml",
        "wizard/create_facturae_view.xml",
        "data/l10n_es_facturae_data.xml",
        "security/ir.model.access.csv"],
    "installable": True,
}
