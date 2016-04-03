# -*- coding: utf-8 -*-
# © 2015-2016 Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
import openerp.tests.common as common
from ..hooks import fill_invoice_sequences
from openerp.addons.l10n_es_account_invoice_sequence.constants import \
    ALLOWED_JOURNAL_TYPES


class TestL10nEsAccountInvoiceSequence(common.TransactionCase):

    def test_create_chart_of_accounts(self):
        company = self.env['res.company'].create(
            {'name': 'Spanish company'})
        wizard = self.env['wizard.multi.charts.accounts'].create(
            {'company_id': company.id,
             'chart_template_id': self.env.ref(
                 'l10n_es.account_chart_template_pymes').id,
             'code_digits': 6,
             'currency_id': self.env.ref('base.EUR').id})
        data = wizard._prepare_all_journals(
            wizard.chart_template_id.id, {}, company.id)
        self.assertTrue(
            all([vals['sequence_id'] for vals in data if
                 vals['type'] in ALLOWED_JOURNAL_TYPES]),
            "Not all company journals have sequence")
        sequence_id = data[0]['sequence_id']
        for journal_vals in data:
            self.assertEqual(journal_vals['sequence_id'], sequence_id)
        self.assertTrue(
            all([vals['invoice_sequence_id'] for vals in data if
                 vals['type'] in ALLOWED_JOURNAL_TYPES]),
            "Not all company journals have invoice sequence")
        # Test post_init_hook
        sequence = self.env['ir.sequence'].create({
            'name': 'Test account move sequence',
            'padding': 3,
            'prefix': 'tAM',
            'company_id': company.id,
        })
        journal = self.env['account.journal'].create({
            'name': 'Test Sales Journal',
            'code': 'tVEN',
            'type': 'sale',
            'sequence_id': sequence.id,
            'company_id': company.id,
        })
        fill_invoice_sequences(self.env.cr, self.registry)
        self.assertTrue(journal.sequence_id)
        self.assertEqual(journal.invoice_sequence_id, sequence)
