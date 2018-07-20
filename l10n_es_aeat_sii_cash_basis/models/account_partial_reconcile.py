# -*- coding: utf-8 -*-
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models
from odoo.tools import config


class AccountPartialReconcile(models.Model):
    _inherit = 'account.partial.reconcile'

    def create_tax_cash_basis_entry(self, value_before_reconciliation):
        if (config['test_enable'] and
                not self.env.context.get('test_sii_cash_basis')):
            # Do nothing when testing other modules
            invoices = []
        else:
            invoices = (
                self.debit_move_id + self.credit_move_id
            ).mapped('invoice_id')
        for invoice in invoices:
            company = invoice.company_id
            if not company.use_connector:
                invoice.send_cash_basis_payment(self)
            else:
                eta = self.env.context.get(
                    'override_eta', company._get_sii_eta()
                )
                new_delay = invoice.sudo().with_context(
                    company_id=company.id
                ).with_delay(
                    eta=eta if not invoice.sii_send_failed else False,
                ).send_cash_basis_payment(self)
                job = self.env['queue.job'].search(
                    [('uuid', '=', new_delay.uuid)], limit=1,
                )
                invoice.sudo().invoice_jobs_ids |= job
        return super(
            AccountPartialReconcile, self,
        ).create_tax_cash_basis_entry(value_before_reconciliation)
