# -*- coding: utf-8 -*-
#########################################################################
#                                                                       #
# Copyright (C) 2012 Factor Libre SL                                    #
#                                                                       #
#This program is free software: you can redistribute it and/or modify   #
#it under the terms of the GNU General Public License as published by   #
#the Free Software Foundation, either version 3 of the License, or      #
#(at your option) any later version.                                    #
#                                                                       #
#This program is distributed in the hope that it will be useful,        #
#but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#GNU General Public License for more details.                           #
#                                                                       #
#You should have received a copy of the GNU General Public License      #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#########################################################################

from osv import osv
from osv import fields


class res_partner(osv.osv):
    _inherit = 'res.partner'

    _columns = {
        'valid_vies_vat': fields.boolean('Vies Valid Vat')
    }

    def onchange_vat(self, cr, uid, ids, vat):
        return {'value': {'valid_vies_vat': False}}

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}

        if 'validated_vies' not in context:
            if 'vat' in vals:
                vals['valid_vies_vat'] = False

        return super(res_partner, self).write(cr, uid, ids, vals, context=context)

res_partner()
