# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2008 ACYSOS S.L. (http://acysos.com) All Rights Reserved.
#                       Pedro Tarrafeta <pedro@acysos.com>
#    Copyright (c) 2012 Servicios Tecnológicos Avanzados (http://www.serviciosbaeza.com)
#                       Pedro Manuel Baeza <pedro.baeza@serviciosbaeza.com>
#    Copyright (c) 2012 Avanzosc (http://www.avanzosc.com)
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
    "name" : "Spanish fiscal year closing",
    "version" : "1.1",
    "author" : "Pexego / Pedro M. Baeza,Odoo Community Association (OCA)",
    "website" : "http://www.pexego.es / http://www.serviciosbaeza.com",
    "category" : "Localisation/Accounting",
    "description": """
Spanish fiscal year closing wizard
    
Replaces the default OpenERP end of year wizards (from account module)
with a more advanced all-in-one wizard that will let the users:
  - Check for unbalanced moves, moves with invalid dates
    or period or draft moves on the fiscal year to be closed.
  - Create the Loss and Profit entry.
  - Create the Net Loss and Profit entry.
  - Create the Closing entry.
  - Create the Opening entry.

It's highly configurable, and comes preconfigured for the current Spanish chart of accounts.

It takes in account deferral method set in account types:
  - None: Nothing is done for this account.
  - Balance: Create account move line with the balance of the year for the account.
  - Detail: Create one account move line for each partner with balance for the account.
  - Unreconciled: Not supported.

Also is stateful, saving all the info about the fiscal year closing, so the
user can cancel and undo the operations easily.

##Serv. Tecnol. Baeza##: Modified for ignoring account moves in 'Other' journey.
    """,
    "license" : "AGPL-3",
    "depends" : [
                    "base",
                    "account",
                    "l10n_es",
                ],
    "init_xml" : [],
    "update_xml" : [
                    "wizard/wizard_run_view.xml",
                    "security/ir.model.access.csv",
                    "security/security.xml",
                    "fyc_workflow.xml",
                    "fyc_view.xml",
                    "hide_account_wizards.xml",
                    
                    ],
    "active": False,
    "installable": True
}

