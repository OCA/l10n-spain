# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
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

from osv import osv

class res_partner(osv.osv):
    _inherit = 'res.partner'

    def create(self, cr, uid, vals, context={}):
        """Sequence only assigned to customer or supplier partners"""
        try:
            if (not vals['ref'] or not vals['ref'].strip()) and (vals['customer'] or vals['supplier']):
                vals['ref'] = self.pool.get('ir.sequence').get(cr, uid, 'res.partner')
        except KeyError:
            vals['ref'] = self.pool.get('ir.sequence').get(cr, uid, 'res.partner')
        return super(res_partner, self).create(cr, uid, vals, context)
res_partner()
