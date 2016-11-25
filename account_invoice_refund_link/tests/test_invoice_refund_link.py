# -*- coding: utf-8 -*-
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.tests.common import TransactionCase


class TestInvoiceRefundLink(TransactionCase):
    def setUp(self, *args, **kwargs):
        super(TestInvoiceRefundLink, self).setUp(*args, **kwargs)
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
        })
        default_invoice_account = self.env['account.account'].search([
            ('internal_type', '=', 'receivable'),
            ('deprecated', '=', False),
        ])[0]
        default_line_account = self.env['account.account'].search([
            ('internal_type', '=', 'other'),
            ('deprecated', '=', False),
        ])[0]
        self.invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'type': 'out_invoice',
            'account_id': default_invoice_account.id,
            'invoice_line_ids': [(0, False, {
                'name': 'Test description',
                'account_id': default_line_account.id,
                'quantity': 1.0,
                'price_unit': 100.0,
            })]
        })
        self.invoice.signal_workflow('invoice_open')
        self.refund_reason = 'The refund reason'

    def test_refund_link(self):
        self.env['account.invoice.refund'].with_context(
            active_ids=self.invoice.ids).create({
                'filter_refund': 'refund',
                'description': 'The refund reason',
            }).invoice_refund()
        refund = self.invoice.refund_invoice_ids[0]
        self.assertEqual(refund.refund_reason, self.refund_reason)
        self.assertEqual(refund.origin_invoice_ids[0], self.invoice)
        self.assertEqual(self.invoice.invoice_line_ids[0],
                         refund.invoice_line_ids[0].origin_line_ids[0])
