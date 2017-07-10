# -*- coding: utf-8 -*-
# Copyright 2004-2010 ISA srl (<http://www.isa.it>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.exceptions import Warning as UserError


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    registration_date = fields.Date(
        'Registration Date',
        states={
            'paid': [('readonly', True)],
            'open': [('readonly', True)],
            'close': [('readonly', True)]
        },
        select=True,
        help="Keep empty to use the current date",
        copy=False)

    def _get_period_from_dates(self):
        self.ensure_one()
        if self.period_id:
            period_id = self.period_id
        else:
            date = self.registration_date or self.date_invoice \
                   or fields.Date.today()
            period_id = self.env['account.period'].find(dt=date)
        return period_id

    @api.multi
    def action_move_create(self):
        for inv in self:
            if inv.type in ('in_invoice', 'in_refund'):
                date_invoice = inv.date_invoice
                reg_date = inv.registration_date
                if not inv.registration_date:
                    if not inv.date_invoice:
                        reg_date = fields.Date.today()
                    else:
                        reg_date = inv.date_invoice
                if date_invoice and reg_date and date_invoice > reg_date:
                    raise UserError(
                        _("The invoice date cannot be later than"
                          " the date of registration!"))
                period_id = inv._get_period_from_dates()
                invoice_values = {'registration_date': reg_date,
                                  'period_id': period_id.id}
                # ----- For in invoice or refund, force the sequence based on
                #       registration date
                if not inv.internal_number:
                    sequence_model = self.pool.get('ir.sequence')
                    invoice_number_context = {
                        'fiscalyear_id': period_id.fiscalyear_id.id
                    }
                    internal_number = sequence_model.next_by_id(
                        self._cr, self._uid, inv.journal_id.sequence_id.id,
                        invoice_number_context
                    )
                    invoice_values.update({'internal_number': internal_number})
                inv.write(invoice_values)

        super(AccountInvoice, self).action_move_create()

        for inv in self:
            if inv.type in ('in_invoice', 'in_refund'):
                mov_date = inv.registration_date or inv.date_invoice or \
                           fields.Date.today()
                inv.move_id.button_cancel()
                period_id = inv._get_period_from_dates()
                inv.move_id.write(
                    {'period_id': period_id.id, 'date': mov_date}
                )
                inv.move_id.button_validate()
        return True

    def _get_account_registration_date(self):
        return self.registration_date or fields.Date.today()
