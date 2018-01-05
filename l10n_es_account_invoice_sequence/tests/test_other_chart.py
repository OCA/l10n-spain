# -*- coding: utf-8 -*-
# Copyright 2015-2017 Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import common
from ..hooks import post_init_hook


@common.at_install(False)
@common.post_install(True)
class TestOtherChart(common.HttpCase):
    def setUp(self):
        super(TestOtherChart, self).setUp()
        self.company = self.env['res.company'].create({
            'name': 'Other chart company',
        })
        self.account_type = self.env['account.account.type'].create({
            'name': 'Test account type',
        })
        self.transfer_account = self.env['account.account.template'].create({
            'name': 'Test transfer account template',
            'code': 'TTA',
            'user_type_id': self.account_type.id,
        })
        # An XML-ID is needed
        self.env['ir.model.data'].create({
            'module': 'l10n_es_account_invoice_sequence',
            'name': 'test_transfer_account_template',
            'model': self.transfer_account._name,
            'res_id': self.transfer_account.id,
        })
        self.chart = self.env['account.chart.template'].create({
            'name': 'Other chart',
            'currency_id': self.env.ref('base.EUR').id,
            'transfer_account_id': self.transfer_account.id,
        })
        self.transfer_account.chart_template_id = self.chart.id
        self.journal_obj = self.env['account.journal']
        self.wizard = self.env['wizard.multi.charts.accounts'].create({
            'company_id': self.company.id,
            'chart_template_id': self.chart.id,
            'code_digits': 6,
            'currency_id': self.env.ref('base.EUR').id,
            'transfer_account_id': self.chart.transfer_account_id.id,
        })
        self.wizard.execute()

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
