# Copyright 2026 Binhex
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestPromissoryNoteCajamar(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.rl = cls.env["res.lang"]
        for lang in ("en_US", "es_ES"):
            if not cls.rl.search([("code", "=", lang)]):
                cls.rl._activate_lang(lang)
        cls.company = cls.env.ref("base.main_company")
        cls.cajamar_layout = (
            "account_promissory_note_cajamar.action_report_promissory_footer_cm"
        )
        cls.report_action = cls.env.ref(
            "account_promissory_note_cajamar.action_report_promissory_footer_cm"
        )
        cls.cash_journal = cls.env["account.journal"].search(
            [("company_id", "=", cls.company.id), ("type", "=", "cash")],
            limit=1,
        )

    def _create_payment(self):
        payment = self.env["account.payment"].create(
            {
                "payment_type": "inbound",
                "payment_method_line_id": (
                    self.cash_journal.inbound_payment_method_line_ids[0].id
                ),
                "amount": 250.50,
                "journal_id": self.cash_journal.id,
                "partner_id": self.env.ref("base.partner_demo").id,
                "date": "2026-08-17",
                "promissory_note": True,
                "date_due": "2026-10-17",
            }
        )
        return payment

    def test_layout_option_added_to_company(self):
        selection = dict(
            self.company._fields[
                "account_check_printing_layout"
            ]._description_selection(self.company.env)
        )
        self.assertIn(self.cajamar_layout, selection)
        self.company.account_check_printing_layout = self.cajamar_layout
        self.assertEqual(
            self.company.account_check_printing_layout, self.cajamar_layout
        )

    def test_layout_option_available_on_journal(self):
        # In 18.0 journal.bank_check_printing_layout is computed from the
        # company's account_check_printing_layout selection.
        self.company.account_check_printing_layout = self.cajamar_layout
        journal_layouts = dict(
            self.cash_journal._fields[
                "bank_check_printing_layout"
            ]._description_selection(self.cash_journal.env)
        )
        self.assertIn(self.cajamar_layout, journal_layouts)

    def test_report_renders(self):
        payment = self._create_payment()
        content, content_type = self.env["ir.actions.report"]._render_qweb_pdf(
            self.report_action.xml_id, res_ids=payment.ids
        )
        self.assertEqual(content_type, "html")
        self.assertGreater(len(content), 0)
