# -*- encoding: utf-8 -*-
##############################################################################
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################
from osv import osv, fields, orm

class account_invoice_series(osv.osv):
	_name='account.invoice.series'
	_columns={
		'name':fields.char('Name', size=32, required=True       	   	),
		'sequence_id': fields.many2one('ir.sequence', 'Invoice Sequence', help="You may create different sequences for different invoice series", required=True),
	}

account_invoice_series()

class account_invoice(osv.osv):
	_name='account.invoice'
	_inherit='account.invoice'
	_columns={
		'series_id': fields.many2one('account.invoice.series', 'Series', required=True, states={'open':[('readonly',True)],'close':[('readonly',True)]}),
	}

	def action_number(self, cr, uid, ids, *args):
		cr.execute('SELECT id, type, number, move_id, reference, series_id ' \
			'FROM account_invoice ' \
			'WHERE id IN ('+','.join(map(str,ids))+')')
		for (id, invtype, number, move_id, reference, series_id) in cr.fetchall():
			if not number:
				if not series_id:
					raise "You need to set an Invoicing Series"
				else:
					inv = self.browse(cr, uid, id)
					number = self.pool.get('ir.sequence').get_id(cr, uid, inv.series_id.sequence_id.id)
				if type in ('in_invoice', 'in_refund'):
					ref = reference
				else:
					ref = self._convert_ref(cr, uid, number)
				cr.execute('UPDATE account_invoice SET number=%s ' \
					'WHERE id=%d', (number, id))
				cr.execute('UPDATE account_move_line SET ref=%s ' \
					'WHERE move_id=%d AND (ref is null OR ref = \'\')',
					(ref, move_id))
				cr.execute('UPDATE account_analytic_line SET ref=%s ' \
					'FROM account_move_line ' \
					'WHERE account_move_line.move_id = %d ' \
						'AND account_analytic_line.move_id = account_move_line.id',
						(ref, move_id))
		return True

account_invoice()


