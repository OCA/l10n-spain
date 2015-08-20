# -*- coding: utf-8 -*-
# (c) 2015 Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from openerp import models, api, _
from openerp.addons.l10n_es_account_invoice_sequence.constants import \
    ALLOWED_JOURNAL_TYPES


class WizardMultiChartsAccounts(models.TransientModel):
    _inherit = 'wizard.multi.charts.accounts'

    @api.model
    def _prepare_all_journals(self, chart_template_id, acc_template_ref,
                              company_id):
        journal_data = super(WizardMultiChartsAccounts, self).\
            _prepare_all_journals(chart_template_id, acc_template_ref,
                                  company_id)
        spanish_charts = [
            self.env.ref('l10n_es.account_chart_template_common').id,
            self.env.ref('l10n_es.account_chart_template_assoc').id,
            self.env.ref('l10n_es.account_chart_template_pymes').id,
            self.env.ref('l10n_es.account_chart_template_full').id,
        ]
        if chart_template_id not in spanish_charts:
            # Discard non spanish companies
            return journal_data
        journal_model = self.env['account.journal']
        # Create unified sequence for journal entries
        generic_journal_seq = self.env.ref(
            'l10n_es_account_invoice_sequence.sequence_spanish_journal')
        journal_seq = generic_journal_seq.copy(
            {'name': _('Journal Entries Sequence'),
             'company_id': company_id})
        for journal_vals in journal_data:
            journal_vals['sequence_id'] = journal_seq.id
            if journal_vals['type'] in ALLOWED_JOURNAL_TYPES:
                journal_vals['invoice_sequence_id'] = (
                    journal_model.create_sequence(journal_vals))
        return journal_data
