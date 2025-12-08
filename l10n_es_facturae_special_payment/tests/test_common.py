# Copyright 2025 (APSL - Nagarro) Bernat Obrador
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import tagged

from odoo.addons.l10n_es_facturae.tests.common import CommonTestBase


@tagged("post_install", "-at_install")
class CommonTestSpecialPayment(CommonTestBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.payment_mode_13 = cls.env["account.payment.mode"].create(
            {
                "name": "Test payment mode 13",
                "bank_account_link": "fixed",
                "fixed_journal_id": cls.journal.id,
                "payment_method_id": cls.payment_method.id,
                "show_bank_account_from_journal": True,
                "facturae_code": "13",
                "refund_payment_mode_id": cls.refund_payment_mode.id,
            }
        )

    def test_facturae_with_special_payment(self):
        self._activate_certificate(self.certificate_password)

        factoring_bank = self.env["res.partner.bank"].create(
            {
                "acc_number": "FR20 1243 1243 1243 1243 1243 123",
                "partner_id": self.company.partner_id.id,
                "bank_id": self.env["res.bank"]
                .search([("bic", "=", "PSSTFRPPXXX")], limit=1)
                .id,
            }
        )

        self.move.payment_mode_id = self.payment_mode_13
        factoring_bank.bank_id.state = self.state
        self.move.facturae_factoring_bank_account_id = factoring_bank
        self.move.facturae_payment_reconciliation_reference = "MI-REF-EMISOR"
        self.move.facturae_debit_reconciliation_reference = "MI-REF-RECEPTOR"

        self.move.action_post()
        self.move.name = "2999/99999"
        generated_facturae = self._create_facturae_file(self.move, force=True)

        ns = {"fe": self.fe}

        iban_xpath = (
            "/fe:Facturae/Invoices/Invoice/PaymentDetails/Installment/"
            "AccountToBeCredited/IBAN"
        )
        iban_node = generated_facturae.xpath(iban_xpath, namespaces=ns)
        self.assertTrue(iban_node)
        expected_iban = "".join(factoring_bank.acc_number.split())
        self.assertEqual(iban_node[0].text, expected_iban)

        payment_ref_xpath = (
            "/fe:Facturae/Invoices/Invoice/PaymentDetails/Installment/"
            "PaymentReconciliationReference"
        )
        payment_ref_node = generated_facturae.xpath(payment_ref_xpath, namespaces=ns)
        self.assertTrue(payment_ref_node)
        self.assertEqual(payment_ref_node[0].text, "MI-REF-EMISOR")

        debit_ref_xpath = (
            "/fe:Facturae/Invoices/Invoice/PaymentDetails/Installment/"
            "DebitReconciliationReference"
        )
        debit_ref_node = generated_facturae.xpath(debit_ref_xpath, namespaces=ns)
        self.assertTrue(debit_ref_node)
        self.assertEqual(debit_ref_node[0].text, "MI-REF-RECEPTOR")
