# -*- encoding: utf-8 -*-
##############################################################################
#
#    Avanzosc - Avanced Open Source Consulting
#    Copyright (C) 2011 - 2012 Avanzosc <http://www.avanzosc.com>
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
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################
{
    "name" : "Invoice from Analytics",
    "version" : "1.0",
    "author" : "Avanzosc",
    "description" : """Possibility to invoice everything from analytics. Changes sales workflow slightly and connects sales with account_invoicing module.
    Features:
    * Creates agreement automatically if the product is going to be invoiced recursively.
    * Different payment deadlines for sale order lines.
    * Changes the menu structure to include recurring invoices under "Accounting/Periodical Processing/Recurring Invoice" menu.
    
    Invoicing types:
    * Invoice once
    * Invoice once but with payment deadlines
    * Invoice recursively
    """,
    "website" : "http://www.avanzosc.com",
    "license" : "GPL-2",
    "category" : "Generic Modules/Accounting",
    "depends" : ["sale",
                 "account_invoicing",
                 "analytic",
                 ],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : ["product_view.xml",
                    "sale_view.xml",
                    "analytic_view.xml",
                    "workflow.xml",
                    "account_menu.xml",
                    "partner_view.xml",
                    "wizard/account_invoice_wiz.xml"],
    "active":False,
    "installable":True,
}
