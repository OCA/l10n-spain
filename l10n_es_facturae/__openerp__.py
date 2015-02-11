# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Alejandro Sanchez (http://www.asr-oss.com) All Rights Reserved.
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
    "name" : "Factura-e File Creation",
    "version" : "1.0",
    "author" : "Alejandro Sanchez",
    "category" : "Localisation/Accounting",
    "description" : """This module creates Factura-e 3.1 files from invoices.
3.1 -> 3.2 converter: http://sedeaplicaciones2.minetur.gob.es/FacturaECon/
******* Module under development *******
Successfully passes format and account validation tests from AEAT: http://sedeaplicaciones2.minetur.gob.es/FacturaE/index.jsp
""",
    "website" : "www.asr-oss.com",
    "license" : "AGPL-3",
    "depends" : ["base", "account"],
    "update_xml" : [
        "country_view.xml",
        "data_res_country.xml",
        "partner_view.xml",
        "res_company.xml",
        "wizard/create_facturae_view.xml"],
    "installable" : True,
}
