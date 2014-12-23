# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, _


class AccountFiscalyear(models.Model):
    _inherit = "account.fiscalyear"

    @api.v7
    def create_period(self, cr, uid, ids, context=None, interval=1):
        recs = self.browse(cr, uid, ids, context)
        recs.create_period(interval=interval)

    @api.v8
    def create_period(self, interval=1):
        res = super(AccountFiscalyear, self).create_period(interval=interval)
        period_model = self.env['account.period']
        for fy in self:
            period_model.create({
                'name':  "%s %s" % (_('Closing Period'), fy.code),
                'code': '%s/%s' % (_('C'), fy.code),
                'date_start': fy.date_stop,
                'date_stop': fy.date_stop,
                'special': True,
                'fiscalyear_id': fy.id})
            period_model.create({
                'name':  "%s %s" % (_('Profit and loss Period'), fy.code),
                'code': '%s/%s' % (_('PL'), fy.code),
                'date_start': fy.date_stop,
                'date_stop': fy.date_stop,
                'special': True,
                'fiscalyear_id': fy.id})
        return res
