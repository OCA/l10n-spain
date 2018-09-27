# Copyright 2016 Pedro M. Baeza
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import common
from odoo import fields


class TestInvoiceSequence(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestInvoiceSequence, cls).setUpClass()
        cls.sequence = cls.env['ir.sequence'].create({
            'name': 'Test account move sequence',
            'padding': 3,
            'prefix': 'tAM',
        })
        cls.invoice_sequence = cls.env['ir.sequence'].create({
            'name': 'Test invoice sequence',
            'padding': 3,
            'prefix': 'tINV',
            'number_next': 5,
        })
        cls.refund_sequence = cls.env['ir.sequence'].create({
            'name': 'Test refund sequence',
            'padding': 3,
            'prefix': 'tREF',
            'number_next': 10,
        })
        cls.journal = cls.env['account.journal'].create({
            'name': 'Test Sales Journal',
            'code': 'tVEN',
            'type': 'sale',
            'sequence_id': cls.sequence.id,
            'update_posted': True,
            'invoice_sequence_id': cls.invoice_sequence.id,
            'refund_inv_sequence_id': cls.refund_sequence.id,
        })
        cls.journal2 = cls.env['account.journal'].create({
            'name': 'Test Sales Journal 2',
            'code': 'tVEN2',
            'type': 'sale',
            'sequence_id': cls.sequence.id,
            'update_posted': True,
            'invoice_sequence_id': cls.invoice_sequence.id,
        })
        cls.account_type = cls.env['account.account.type'].create({
            'name': 'Test',
            'type': 'receivable',
        })
        cls.account = cls.env['account.account'].create({
            'name': 'Test account',
            'code': 'TEST',
            'user_type_id': cls.account_type.id,
            'reconcile': True,
        })
        cls.account_income = cls.env['account.account'].create({
            'name': 'Test income account',
            'code': 'INCOME',
            'user_type_id': cls.env['account.account.type'].create(
                {'name': 'Test income'}).id,
        })
        cls.env.user.company_id.chart_template_id = cls.env.ref(
            'l10n_es.account_chart_template_pymes'
        ).id  # trick the installed chart template

    def test_move_sequence(self):
        move = self.env['account.move'].create({
            'date': fields.Date.today(),
            'journal_id': self.journal.id,
            'name': '/',
            'ref': 'l10n_es_account_invoice_sequence',
            'state': 'draft',
            'line_ids': [(0, 0, {
                'account_id': self.account.id,
                'credit': 1000,
                'debit': 0,
                'name': 'Test',
                'ref': 'l10n_es_account_invoice_sequence',
            }), (0, 0, {
                'account_id': self.account.id,
                'credit': 0,
                'debit': 1000,
                'name': 'Test',
                'ref': 'l10n_es_account_invoice_sequence',
            })]})
        move.post()
        self.assertEqual(move.name[:3], 'tAM')

    def test_invoice_sequence(self):
        invoice = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'account_id': self.account.id,
            'company_id': self.env.user.company_id.id,
            'currency_id': self.env.user.company_id.currency_id.id,
            'partner_id': self.env['res.partner'].create({'name': 'Test'}).id,
            'invoice_line_ids': [(0, 0, {
                'account_id': self.account_income.id,
                'name': 'Test line',
                'price_unit': 50,
                'quantity': 10,
            })]
        })
        self.assertEqual(invoice.sequence_number_next, '005')
        invoice.action_invoice_open()
        self.assertEqual(invoice.number[:4], 'tINV')
        self.assertEqual(invoice.move_id.name[:3], 'tAM')
        self.assertEqual(invoice.move_id.ref[:4], 'tINV')
        invoice2 = invoice.copy()
        self.assertNotEqual(invoice.number, invoice2.number)
        # Cancel invoice and try to unlink
        invoice.action_invoice_cancel()
        invoice.unlink()  # This shouldn't raise error
        self.assertFalse(invoice.exists())

    def test_refund_sequence_01(self):
        invoice = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'account_id': self.account.id,
            'type': 'out_refund',
            'company_id': self.env.user.company_id.id,
            'currency_id': self.env.user.company_id.currency_id.id,
            'partner_id': self.env['res.partner'].create({'name': 'Test'}).id,
            'invoice_line_ids': [(0, 0, {
                'account_id': self.account.id,
                'name': 'Test line',
                'price_unit': 50,
                'quantity': 10,
            })]
        })
        self.assertEqual(invoice.sequence_number_next, '010')
        invoice.action_invoice_open()
        self.assertEqual(invoice.number[:4], 'tREF')
        self.assertEqual(invoice.move_id.name[:3], 'tAM')
        self.assertEqual(invoice.move_id.ref[:4], 'tREF')

    def test_refund_sequence_02(self):
        invoice = self.env['account.invoice'].create({
            'journal_id': self.journal2.id,
            'account_id': self.account.id,
            'type': 'out_refund',
            'company_id': self.env.user.company_id.id,
            'currency_id': self.env.user.company_id.currency_id.id,
            'partner_id': self.env['res.partner'].create({'name': 'Test'}).id,
            'invoice_line_ids': [(0, 0, {
                'account_id': self.account.id,
                'name': 'Test line',
                'price_unit': 50,
                'quantity': 10,
            })]
        })
        invoice.action_invoice_open()
        self.assertEqual(invoice.number[:4], 'tINV')
        self.assertEqual(invoice.move_id.name[:3], 'tAM')
        self.assertEqual(invoice.move_id.ref[:4], 'tINV')
