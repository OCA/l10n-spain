# Copyright 2015-2018 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import common
from odoo import exceptions
from ..hooks import post_init_hook


class TestCreateChart(common.SavepointCase):
    at_install = False
    post_install = True

    @classmethod
    def setUpClass(cls):
        super(TestCreateChart, cls).setUpClass()
        cls.company = cls.env['res.company'].create(
            {'name': 'Spanish company'},
        )
        cls.chart = cls.env.ref('l10n_es.account_chart_template_pymes')
        cls.journal_obj = cls.env['account.journal']
        cls.env.user.company_id = cls.company.id
        cls.chart.try_loading_for_current_company()

    def test_create_chart_of_accounts(self):
        journals = self.journal_obj.search([
            ('company_id', '=', self.company.id),
        ])
        self.assertTrue(
            all([j.sequence_id for j in journals]),
            "Not all company journals have sequence",
        )
        sequence = journals[:1].sequence_id
        for journal in journals:
            self.assertEqual(
                journal.sequence_id, sequence,
                "Journal '{}' doesn't have the same sequence.".format(
                    journal.name
                )
            )
            self.assertFalse(journal.refund_sequence)
        inv_journals = journals.filtered(
            lambda x: x.type in journals._get_invoice_types()
        )
        self.assertTrue(
            all([j.invoice_sequence_id for j in inv_journals]),
            "Not all invoice journals have invoice sequence",
        )
        self.assertFalse(
            any([j.invoice_sequence_id for j in (journals - inv_journals)]),
            "None of the normal journals have invoice sequence",
        )
        self.assertTrue(
            all([j.refund_inv_sequence_id for j in inv_journals]),
            "Not all invoice journals have refund invoice sequence",
        )
        self.assertFalse(
            any([j.refund_inv_sequence_id for j in (journals - inv_journals)]),
            "Any of the normal journals have refund invoice sequence",
        )
        self.assertTrue(all(
            [j.refund_inv_sequence_id != j.invoice_sequence_id
             for j in inv_journals],
        ))

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
        self.assertTrue(journal.sequence_id)
        self.assertEqual(journal.invoice_sequence_id, sequence)
        self.assertEqual(journal.refund_inv_sequence_id, sequence)

    def test_new_journal(self):
        prev_journal = self.journal_obj.search(
            [('company_id', '=', self.company.id)], limit=1,
        )
        journal = self.journal_obj.create({
            'name': 'Test journal',
            'code': 'T',
            'type': 'general',
            'company_id': self.company.id,
        })
        self.assertEqual(journal.sequence_id, prev_journal.sequence_id)

    def test_journal_constrains(self):
        other_company = self.env['res.company'].create(
            {'name': 'Other company'},
        )
        sequence = self.env['ir.sequence'].create({
            'name': 'Test sequence',
            'code': 'TEST',
            'company_id': other_company.id,
        })
        with self.assertRaises(exceptions.ValidationError):
            self.journal_obj.create({
                'name': 'Test journal',
                'code': 'T',
                'type': 'general',
                'invoice_sequence_id': sequence.id,
                'company_id': self.company.id,
            })
        with self.assertRaises(exceptions.ValidationError):
            self.journal_obj.create({
                'name': 'Test journal 2',
                'code': 'T 2',
                'type': 'general',
                'refund_inv_sequence_id': sequence.id,
                'company_id': self.company.id,
            })
