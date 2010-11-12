# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2008 ACYSOS S.L. (http://acysos.com) All Rights Reserved.
#                       Pedro Tarrafeta <pedro@acysos.com>
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
    "name" : "Spanish Fiscal Year Closing",
    "version" : "1.0",
    "author" : "Pexego",
    "website" : "",
    "category" : "Localisation/Europe",
    "description": """NOTA: NO ADAPTADO TODAVÍA A LA VERSIÓN 6.0
Spanish Fiscal Year Closing Wizard
    
Replaces the default OpenERP end of year wizards (from account module)
with a more advanced all-in-one wizard that will let the users:
  - Check for unbalanced moves, moves with invalid dates
    or period or draft moves on the fiscal year to be closed.
  - Create the Loss and Profit entry.
  - Create the Net Loss and Profit entry.
  - Create the Closing entry.
  - Create the Opening entry.

It's hightly configurable, and comes preconfigured for the current Spanish chart of accounts.

Also is stateful, saving all the info about the fiscal year closing, so the
user can cancel and undo the operations easily.
    """,
    "license" : "GPL-3",
    "depends" : [
                    "base",
                    "account",
                    "l10n_es",
                ],
    "init_xml" : [],
    "update_xml" : [
                    "security/ir.model.access.csv",
                    "fyc_workflow.xml",
                    "fyc_wizard.xml",
                    "fyc_view.xml",
                    "hide_account_wizards.xml",
                    ],
    "active": False,
    "installable": True
}

