# Copyright 2015-2020 Pedro M. Baeza
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import common

from ..hooks import post_init_hook


class TestOtherChart(common.SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestOtherChart, cls).setUpClass()
        cls.company = cls.env["res.company"].create({"name": "Other chart company"})
        cls.chart = cls.env["account.chart.template"].create(
            {
                "name": "Other chart",
                "currency_id": cls.env.ref("base.EUR").id,
                "bank_account_code_prefix": "572",
                "cash_account_code_prefix": "570",
                "transfer_account_code_prefix": "572999",
            }
        )
        # This is needed for avoiding an error on the chart template loading
        cls.transfer_acc_tmpl = cls.env["account.account.template"].create(
            {
                "name": "Transfer account",
                "code": "572999",
                "chart_template_id": cls.chart.id,
            }
        )
        cls.env["ir.model.data"].create(
            {
                "name": "test_transfer_acc_tmpl",
                "module": "l10n_es_account_invoice_sequence",
                "model": "account.account.template",
                "res_id": cls.transfer_acc_tmpl.id,
            }
        )
        cls.journal_obj = cls.env["account.journal"]
        cls.env.user.company_id = cls.company.id
        # cls.chart.try_loading()

    def test_create_chart_of_accounts(self):
        journals = self.journal_obj.search([("company_id", "=", self.company.id)])
        self.assertFalse(any([j.invoice_sequence_id for j in journals]))
        self.assertFalse(any([j.refund_inv_sequence_id for j in journals]))

    def test_post_init_hook(self):
        sequence = self.env["ir.sequence"].create(
            {
                "name": "Test account move sequence",
                "padding": 3,
                "prefix": "tAM",
                "company_id": self.company.id,
            }
        )
        journal = self.env["account.journal"].create(
            {
                "name": "Test Sale Journal",
                "code": "TSJ",
                "type": "sale",
                "secure_sequence_id": sequence.id,
            }
        )
        post_init_hook(self.env.cr, self.registry)
        # Test that the sequence is not altered
        self.assertEqual(journal.secure_sequence_id, sequence)

    def test_new_journal(self):
        prev_journal = self.journal_obj.search(
            [("company_id", "=", self.company.id)], limit=1
        )
        journal = self.journal_obj.create(
            {
                "name": "Test journal",
                "code": "T",
                "type": "general",
                "company_id": self.company.id,
            }
        )
        self.assertNotEqual(journal.secure_sequence_id, prev_journal.secure_sequence_id)

    def test_invoice(self):
        sequence = self.env["ir.sequence"].create(
            {"name": "Test account move sequence", "padding": 3, "prefix": "tAM"}
        )
        journal = self.env["account.journal"].create(
            {
                "name": "Test Sales Journal",
                "code": "tVEN",
                "type": "sale",
                "secure_sequence_id": sequence.id,
            }
        )
        account = self.env["account.account"].create(
            {"name": "Test account", "code": "TEST", "reconcile": True}
        )
        account_income = self.env["account.account"].create(
            {"name": "Test income account", "code": "INCOME"}
        )
        partner = self.env["res.partner"].create(
            {"name": "Test", "property_account_receivable_id": account.id}
        )
        invoice = self.env["account.move"].create(
            {
                "journal_id": journal.id,
                "company_id": self.env.user.company_id.id,
                "currency_id": self.env.user.company_id.currency_id.id,
                "partner_id": partner.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": account_income.id,
                            "name": "Test line",
                            "price_unit": 50,
                            "quantity": 10,
                        },
                    )
                ],
            }
        )
        invoice.action_post()
        number = invoice.number
        self.assertEqual(invoice.invoice_number, number)
        self.assertNotEqual(invoice.journal_id.name, number)
        invoice.button_cancel()
        # simulate draft button as calling it in tests fail due to do_in_draft
        self.assertEqual(invoice.number, number)
        self.assertEqual(invoice.invoice_number, number)
        self.assertNotEqual(invoice.journal_id.name, number)
