# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2015-TODAY MINORISA (http://www.minorisa.net) All Rights Reserved.
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

from openerp.osv import osv, fields


class AeatSiiMappingRegistrationKeys(osv.Model):
    _name = 'aeat.sii.mapping.registration.keys'
    _description = 'Aeat SII Invoice Registration Keys'

    _columns = {

        'code': fields.char(string='Code', required=True, size=128),
        'name': fields.char(string='Name', size=128),
        'type': fields.selection([('sale', 'Sale'), ('purchase', 'Purchase')], 'Type', required=True)
    }

    # type = fields.Selection([('sale','Sale'),('purchase','Purchase'),('all','All')],'Type',required=True)


    def name_get(self, cr, uid, ids, context=None):

        if context is None:
            context = {}
        reads = self.read(cr, uid, ids, ['code', 'name'], context=context)
        res = []
        for record in reads:
            name = u'[{}]-{}'.format(record.get('code'), record.get('name'))
            res.append(tuple([record['id'], name]))
        return res
