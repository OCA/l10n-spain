# -*- coding: utf-8 -*-
# Copyright 2016-2017 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import _, api, models


class WizardMultiChartsAccounts(models.TransientModel):
    _inherit = 'wizard.multi.charts.accounts'

    @api.multi
    def _create_bank_journals_from_o2m(self, company, acc_template_ref):
        """Write the same sequence also for the bank and cash journals."""
        journal_model = self.env['account.journal']
        journals = journal_model.search([('company_id', '=', company.id)])
        res = super(
            WizardMultiChartsAccounts, self
        )._create_bank_journals_from_o2m(
            company, acc_template_ref,
        )
        journals2 = journal_model.search([('company_id', '=', company.id)])
        new_journals = journals2 - journals
        sequence = self.env['ir.sequence'].search([
            ('name', '=', _('Journal Entries Sequence')),
            ('company_id', '=', company.id)
        ], limit=1,
        )
        new_journals.write({
            'sequence_id': sequence.id,
            'refund_sequence': False,
        })
        return res
