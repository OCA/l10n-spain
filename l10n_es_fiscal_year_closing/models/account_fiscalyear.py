# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.osv import orm
from openerp.tools.translate import _


class AccountFiscalyear(orm.Model):
    _inherit = "account.fiscalyear"

    def create_period(self, cr, uid, ids, context=None, interval=1):
        res = super(AccountFiscalyear, self).create_period(
            cr, uid, ids, interval=interval, context=context)
        period_model = self.pool['account.period']
        for fy in self.browse(cr, uid, ids, context=context):
            period_model.create(
                cr, uid,
                {'name':  "%s %s" % (_('Closing Period'), fy.code),
                 'code': '%s/%s' % (_('C'), fy.code),
                 'date_start': fy.date_stop,
                 'date_stop': fy.date_stop,
                 'special': True,
                 'fiscalyear_id': fy.id}, context=context)
            period_model.create(
                cr, uid,
                {'name':  "%s %s" % (_('Profit and loss Period'), fy.code),
                 'code': '%s/%s' % (_('PL'), fy.code),
                 'date_start': fy.date_stop,
                 'date_stop': fy.date_stop,
                 'special': True,
                 'fiscalyear_id': fy.id}, context=context)
        return res
