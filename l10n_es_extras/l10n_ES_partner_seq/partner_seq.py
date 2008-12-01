# -*- encoding: utf-8 -*-

from osv import osv, fields

class res_partner(osv.osv):
    _inherit = 'res.partner'

    def create(self, cr, uid, vals, context={}):
        """Sequence only assigned to customer or supplier partners"""
        if (not vals['ref'] or not vals['ref'].strip()) and (vals['customer'] or vals['supplier']):
            vals['ref'] = self.pool.get('ir.sequence').get(cr, uid, 'res.partner')
        return super(res_partner, self).create(cr, uid, vals, context)
res_partner()
