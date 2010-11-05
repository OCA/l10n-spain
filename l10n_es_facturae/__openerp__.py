# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Alejandro Sanchez (http://www.asr-oss.com) All Rights Reserved.
#                       Alejandro Sanchez <alejandro@asr-oss.com>
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name" : "Factura-e File Creation",
    "version" : "1.0",
    "author" : "Alejandro Sanchez",
    "category" : "Localisation/Accounting",
    "description" : """This module creates Factura-e files from invoices.
******* Module under development *******
Successfully passes format and account validation tests from AEAT: http://www11.mityc.es/FacturaE/ValidarCompleto
""",
    "website" : "www.asr-oss.com",
    "license" : "GPL-3",
    "depends" : ["account"],
    "init_xml" : ["data_res_country.xml"],
    "demo_xml" : [],
    "update_xml" : [
        "account_wizard.xml",
        "account_invoice_view.xml",
        "country_view.xml",],
    "installable" : True,
    "active" : False,
}
