# -*- coding: utf-8 -*-
# (c) 2015 Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
import openerp.tests.common as common
from openerp.addons.l10n_es_account_invoice_sequence.constants import \
    ALLOWED_JOURNAL_TYPES


class TestL10nEsAccountInvoiceSequence(common.TransactionCase):

    def setUp(self):
        super(TestL10nEsAccountInvoiceSequence, self).setUp()

    def test_create_chart_of_accounts(self):
        company = self.env['res.company'].create(
            {'name': 'Spanish company'})
        wizard = self.env['wizard.multi.charts.accounts'].create(
            {'company_id': company.id,
             'chart_template_id': self.env.ref(
                 'l10n_es.account_chart_template_pymes').id,
             'code_digits': 6,
             'currency_id': self.env.ref('base.EUR').id})
        wizard.execute()
        journals = self.env['account.journal'].search(
            [('company_id', '=', company.id),
             ('type', 'in', ALLOWED_JOURNAL_TYPES)])
        self.assertTrue(
            all([j.sequence_id for j in journals]),
            "Not all company journals have sequence")
        sequence = journals[:1].sequence_id
        for journal in journals:
            self.assertEqual(journal.sequence_id, sequence)
        self.assertTrue(
            all([j.invoice_sequence_id for j in journals]),
            "Not all company journals have invoice sequence")
