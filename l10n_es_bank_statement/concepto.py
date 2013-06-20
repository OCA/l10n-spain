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

"""
C43 format (bank statement file) concepts
"""

from osv import osv, fields


class l10n_es_extractos_concepto(osv.osv):
    """
    C43 format concepts, used to map codes from the C43 bank statement file
    to OpenERP accounts.
    """

    _name = 'l10n.es.extractos.concepto'
    _description = 'C43 codes'

    _columns = {
        'code': fields.char('Concept code', size=2, select=True, required=True, help='2 digits code of the concept defined in the file of C43 bank statements'),
        'name': fields.char('Concept name', size=64, select=True, required=True),
        'account_id': fields.many2one('account.account', 'Account associated to the concept', domain=[('type','<>','view'), ('type', '<>', 'closed')], select=True, required=True,
                            help='Default account to be associated with the concept when the file of C43 bank statements is imported'),
        'company_id': fields.many2one('res.company', 'Company', required=True),
    }

    def _default_company_id(self, cr, uid, context={}):
        """
        Gets the default company id
        """
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        if user.company_id:
            return user.company_id.id
        return self.pool.get('res.company').search(cr, uid, [('parent_id', '=', False)])[0]

    _defaults = {
        'company_id': _default_company_id,
    }

l10n_es_extractos_concepto()

