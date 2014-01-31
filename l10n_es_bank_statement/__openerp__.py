# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) All rights reserved:
#        2009      Zikzakmedia S.L. (http://zikzakmedia.com)
#                  Jordi Esteve <jesteve@zikzakmedia.com>
#        2010-2013 Pexego Sistemas Informáticos
#                  Borja López Soilán <borjals@pexego.es>
#                  Alberto Luengo Cabanillas <alberto@pexego.es>
#        2013-2014 Servicios Tecnológicos Avanzados (http://serviciosbaeza.com)
#                  Pedro Manuel Baeza <pedro.baeza@serviciosbaeza.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
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
    "name" : "Extractos bancarios españoles",
    "version" : "3.0",
    "author" : "Spanish localization team",
    "website" : "https://launchpad.net/openerp-spain",
    "category" : "Localisation/Accounting",
    "description" : """
Importación y tratamiento de los extractos bancarios españoles que siguen la
normativa C43 de la 'Asociación Española de la Banca'. Puede consultarse el
formato completo aquí:

https://docs.bankinter.com/stf/plataformas/empresas/gestion/ficheros/formatos_fichero/norma_43_castellano.pdf

**AVISO:** Este módulo requiere de varios módulos del repositorio de código:

https://code.launchpad.net/~banking-addons-team/banking-addons/bank-statement-reconcile-70

-- Old description --
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
    "license" : "AGPL-3",
    "depends" : [
        "l10n_es",
        'account_statement_base_import',
    ],
    "demo" : [],
    "data" : [
        #"extractos_view.xml",
        #"import_c43_file_view.xml",
        #"security/ir.model.access.csv",
        #"security/concepto_security.xml"
    ],
    "installable" : True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
