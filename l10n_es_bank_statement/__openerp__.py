# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2010 Pexego Sistemas Informáticos. All Rights Reserved
#                       Borja López Soilán <borjals@pexego.es>
#    Copyright (c) 2011 Pexego Sistemas Informáticos. All Rights Reserved
#                       Alberto Luengo Cabanillas <alberto@pexego.es>
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
    "name" : "Spanish Bank Statements Importation",
    "version" : "2.0",
    "author" : "Zikzakmedia, Pexego, Acysos, NaN·tic",
    "category" : "Localisation/Accounting",
    "description" : """
Module for the importation of Spanish bank statements following the C43 normative of the 'Asociación Española de la Banca'.
    
    Adds a wizard to the bank statements to perform the importation. The imported file gets attached to the given bank statement.
    It allows to define default accounting codes for the concepts defined in the C43 bank statement file.

    The search of the entries to reconcile (and partner) is done like this:
        1) Unreconciled entries with the given reference and amount. The reference is taken from the 'conceptos' or 'referencia2' fields of the statement.
        2) Unreconciled entries with (a partner with) the given VAT number and amount.
           These fields are tested to find a valid spanish VAT:
              - First 9 characters of 'referencia1' (Banc Sabadell)
              - First 9 characters of 'conceptos' (La Caixa)
              - Characters [21:30] of 'conceptos' (Caja Rural del Jalón)
        3) Unreconciled entries with the given amount.

    If no partner is found, the default account defined for the concept is used.

    The module also adds a wizard in Financial Management/Configuration/C43 bank statements to import the default statement concepts, that must be run after creating the spanish chart of accounts (l10n_es module).
    """,
    "website" : "www.zikzakmedia.com / www.pexego.es / www.acysos.com / www.nan-tic.com",
    "license" : "AGPL-3",
    "depends" : [
        "account",
        "account_voucher",
        "l10n_es",
        "nan_account_bank_statement",
        ],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
        "extractos_view.xml",
        "import_c43_file_view.xml",
        "security/ir.model.access.csv",
        "security/concepto_security.xml"
        ],
    "installable" : True,
    "active" : False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
