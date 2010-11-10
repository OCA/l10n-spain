# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2010 Pexego Sistemas Informáticos. All Rights Reserved
#                       Borja López Soilán <borjals@pexego.es>
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

"""
C43 format concepts and extension of the bank statement lines.
"""

from osv import osv
import tools
import os



class l10n_es_extractos_import_wizard(osv.osv_memory):
    """
    Wizard to import the XML file defining the statement concepts (concepto)
    """

    _name = 'l10n.es.extractos.import.wizard'

    def action_import(self, cr, uid, ids, context=None):
        try:
            fp = tools.file_open(os.path.join('l10n_es_bank_statement', 'extractos_conceptos.xml'))
        except IOError, ex:
            return {}
        idref = {}
        tools.convert_xml_import(cr, 'l10n_es_bank_statement', fp,  idref, 'init', noupdate=True)
        return {}

l10n_es_extractos_import_wizard()

