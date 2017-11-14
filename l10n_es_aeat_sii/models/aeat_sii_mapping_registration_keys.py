# -*- coding: utf-8 -*-
# Copyright 2017 MINORISA (http://www.minorisa.net)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

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
