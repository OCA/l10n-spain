#!/usr/bin/env python
# -*- coding: utf-8 -*-

from osv import osv, fields

class res_partner(osv.osv):
	_inherit = 'res.partner'
	_defaults = {
		#'ref': lambda *a: '[Auto]',
				}  

	def create(self, cr, uid, vals, context={}):
		#if vals['ref'] == '[Auto]' or not vals['name'].strip() or not vals['name']:
		if not vals['ref'] or not vals['ref'].strip():
			vals['ref'] = self.pool.get('ir.sequence').get(cr, uid, 'res.partner')
		return super(res_partner, self).create(cr, uid, vals, context)	
res_partner()
