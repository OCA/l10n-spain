# -*- coding: utf-8 -*-
# Copyright 2017 Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2017 FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from openerp import api, models

_logger = logging.getLogger(__name__)

try:
    from openerp.addons.connector.queue.job import job
    from openerp.addons.connector.session import ConnectorSession
except ImportError:
    _logger.debug('Can not `import connector`.')
    import functools

    def empty_decorator_factory(*argv, **kwargs):
        return functools.partial
    job = empty_decorator_factory


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.multi
    def reconcile_partial(
            self, type='auto', writeoff_acc_id=False, writeoff_period_id=False,
            writeoff_journal_id=False):
        queue_obj = self.env['queue.job']
        res = super(AccountMoveLine, self).reconcile_partial(
            type=type, writeoff_acc_id=writeoff_acc_id,
            writeoff_period_id=writeoff_period_id,
            writeoff_journal_id=writeoff_journal_id)
        for move in self:
            if move.invoice:
                if move.invoice.sii_registration_key.code == '07':
                    company = move.invoice.company_id
                    if company.sii_enabled:
                        if not company.use_connector:
                            move.invoice.send_recc_payment(move)
                        else:
                            eta = company._get_sii_eta()
                            session = ConnectorSession.from_env(self.env)
                            new_delay = send_recc_payment_job.delay(
                                session, 'account.move.line', move.id, eta=eta)
                            queue_ids = queue_obj.search([
                                ('uuid', '=', new_delay)
                            ], limit=1)
                            move.invoice.invoice_jobs_ids |= queue_ids
        return res


@job(default_channel='root.invoice_recc_payment_sii')
def send_recc_payment_job(session, model_name, move_id):
    model = session.env[model_name]
    move = model.browse(move_id)
    if move.exists() and move.invoice:
        move.invoice.send_recc_payment(move)
