# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP - Account renumber wizard
#    Copyright (C) 2012 Eficent (www.eficent.com). All Rights Reserved
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
        "name" : "Account invoice sequence fix",
        "version" : "0.1",
        "author" : "Eficent,Odoo Community Association (OCA)",
        "website" : "http://www.eficent.com",
        "category" : "Enterprise Specific Modules",
        "description": """
This module should be used by anyone who has initiated an OpenERP with spanish localization modules 
did not install the module "nan_account_invoice_sequence", and has already accepted several invoices.
In this circumstance, once the module "nan_account_invoice_sequence" is installed the invoices already created 
will loose the invoice number, because it was the move number and the nan module adds a separate field to store the 
invoice number.
  
What this module will do i wizard will do is select all invoices with moves and copy the move number to the new invoice number field.
This wizard should be run just after module "nan_account_invoice_sequence" has been installed, and no new invoices have been produced in the system.
It is highly recommended that once the wizard has been run, the module should be removed, so as to avoid any furter use that might overwrite the existing invoice numbers.

            """,
        "depends" : [
                'nan_account_invoice_sequence',
            ],
        "init_xml" : [
            ],
        "demo_xml" : [ ],
        "update_xml" : [
                'invoice_repair_wizard.xml',
            ],
        "installable": True
}
