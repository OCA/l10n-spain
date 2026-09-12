# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountPromissoryNoteCaixabank(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass(chart_template_ref="l10n_es.account_chart_template_pymes")
        cls.layout_key = (
            "account_promissory_note_caixabank.action_report_promissory_footer_cb"
        )
        cls.report = cls.env.ref(cls.layout_key)

    def test_caixabank_report_prints_its_own_block(self):
        """Printing the layout must render the module's own content.

        The module's template appends the amount in words (num2words) to the
        base A4 promissory note, so rendering it must include that output.
        """
        journal = self.company_data["default_journal_bank"]
        payment = self.env["account.payment"].create(
            {
                "payment_type": "outbound",
                "partner_id": self.partner_a.id,
                "journal_id": journal.id,
                "payment_method_line_id": journal.outbound_payment_method_line_ids[
                    :1
                ].id,
                "amount": 1234.56,
                "date": fields.Date.today(),
                "promissory_note": True,
                "date_due": fields.Date.today(),
            }
        )
        html, _ = (
            self.env["ir.actions.report"]
            .with_context(lang="en_US")
            ._render_qweb_html(self.report, payment.ids)
        )
        # Amount in words is produced only by this module's template block.
        self.assertIn(b"thousand", html)
        self.assertIn(b"1234", html.replace(b",", b"").replace(b".", b""))
