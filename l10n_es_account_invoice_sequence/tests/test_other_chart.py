# -*- coding: utf-8 -*-
# Copyright 2015-2017 Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

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
        cls.transfer_account = cls.env['account.account.template'].create({
            'name': 'Test transfer account template',
            'code': 'TTA',
            'user_type_id': cls.account_type.id,
        })
        # An XML-ID is needed
        cls.env['ir.model.data'].create({
            'module': 'l10n_es_account_invoice_sequence',
            'name': 'test_transfer_account_template',
            'model': cls.transfer_account._name,
            'res_id': cls.transfer_account.id,
        })
        cls.chart = cls.env['account.chart.template'].create({
            'name': 'Other chart',
            'currency_id': cls.env.ref('base.EUR').id,
            'transfer_account_id': cls.transfer_account.id,
        })
        cls.transfer_account.chart_template_id = cls.chart.id
        cls.journal_obj = cls.env['account.journal']
        cls.wizard = cls.env['wizard.multi.charts.accounts'].create({
            'company_id': cls.company.id,
            'chart_template_id': cls.chart.id,
            'code_digits': 6,
            'currency_id': cls.env.ref('base.EUR').id,
            'transfer_account_id': cls.chart.transfer_account_id.id,
        })
        cls.wizard.execute()

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
