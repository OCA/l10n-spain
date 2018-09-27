# Copyright 2015-2018 Pedro M. Baeza
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import common
from ..hooks import post_init_hook


@common.at_install(False)
@common.post_install(True)
class TestOtherChart(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestOtherChart, cls).setUpClass()
        cls.company = cls.env['res.company'].create({
            'name': 'Other chart company',
        })
        cls.account_type = cls.env['account.account.type'].create({
            'name': 'Test account type',
        })
        cls.chart = cls.env['account.chart.template'].create({
            'name': 'Other chart',
            'currency_id': cls.env.ref('base.EUR').id,
            'bank_account_code_prefix': '572',
            'cash_account_code_prefix': '570',
            'transfer_account_code_prefix': '572',
        })
        cls.journal_obj = cls.env['account.journal']
        cls.env.user.company_id = cls.company.id
        cls.chart.try_loading_for_current_company()

    def test_create_chart_of_accounts(self):
        journals = self.journal_obj.search([
            ('company_id', '=', self.company.id),
        ])
        self.assertFalse(any([j.invoice_sequence_id for j in journals]))
        self.assertFalse(any([j.refund_inv_sequence_id for j in journals]))

    def test_post_init_hook(self):
        sequence = self.env['ir.sequence'].create({
            'name': 'Test account move sequence',
            'padding': 3,
            'prefix': 'tAM',
            'company_id': self.company.id,
        })
        journal = self.env['account.journal'].create({
            'name': 'Test Sales Journal',
            'code': 'tVEN',
            'type': 'sale',
            'sequence_id': sequence.id,
            'refund_sequence_id': sequence.id,
            'company_id': self.company.id,
        })
        post_init_hook(self.env.cr, self.registry)
        # Test that the sequence is not altered
        self.assertEqual(journal.sequence_id, sequence)

    def test_new_journal(self):
        prev_journal = self.journal_obj.search(
            [('company_id', '=', self.company.id)], limit=1,
        )
        self.assertTrue(prev_journal)
        journal = self.journal_obj.create({
            'name': 'Test journal',
            'code': 'T',
            'type': 'general',
            'company_id': self.company.id,
        })
        self.assertNotEqual(journal.sequence_id, prev_journal.sequence_id)
