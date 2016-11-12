# -*- coding: utf-8 -*-
# © 2004-2011 Pexego Sistemas Informáticos. (http://pexego.es)
# © 2012 NaN·Tic  (http://www.nan-tic.com)
# © 2013 Acysos (http://www.acysos.com)
# © 2013 Joaquín Pedrosa Gutierrez (http://gutierrezweb.es)
# © 2014-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
#             (http://www.serviciosbaeza.com)
# © 2016 Antiun Ingenieria S.L. - Antonio Espinosa
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, api, models


class AccountPeriod(models.Model):
    _inherit = "account.period"

    @api.multi
    def assign_quarter(self):
        quarters = self._fields['quarter'].selection
        for period in self:
            ds = fields.Date.from_string(period.date_start)
            period.quarter = quarters[(ds.month - 1)/3][0]
        return True

    quarter = fields.Selection(
        [('first', 'First'),
         ('second', 'Second'),
         ('third', 'Third'),
         ('fourth', 'Fourth')], 'Quarter')


class AccountFiscalyear(models.Model):
    _inherit = "account.fiscalyear"

    @api.multi
    def create_period3(self):
        return self.create_period(interval=3)

    @api.v7
    def create_period(self, cr, uid, ids, context=None, interval=1):
        recs = self.browse(cr, uid, ids, context=context)
        recs.create_period(interval=interval)

    @api.v8
    def create_period(self, interval=1):
        period_obj = self.env['account.period']
        periods_before = period_obj.search([])
        super(AccountFiscalyear, self).create_period(interval=interval)
        periods_after = period_obj.search([])
        new_periods = periods_after - periods_before
        new_periods.assign_quarter()
        return True
