# Copyright 2026 Ozono Multimedia - Iván Antón
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo.exceptions import UserError

from odoo.addons.l10n_es_verifactu_oca.tests.common import TestVerifactuCommon


class TestVerifactuOperationDate(TestVerifactuCommon):
    """Test operation date functionality in VERIFACTU invoices."""

    def test_operation_date_validation(self):
        """Test that operation date cannot be greater than invoice date."""
        self._activate_certificate(self.certificate_password)
        invoice = self._create_test_invoice()
        invoice.aeat_state = "not_sent"
        invoice.date = invoice.invoice_date + timedelta(days=1)

        with self.assertRaisesRegex(
            UserError,
            r"(operation date cannot be greater|fecha de operación no puede ser posterior)",
        ):
            invoice.action_post()

    def test_operation_date_in_dict(self):
        """Test that FechaOperacion is included when date < invoice_date."""
        self._activate_certificate(self.certificate_password)
        invoice = self._create_test_invoice()
        operation_date = invoice.invoice_date - timedelta(days=1)
        invoice.date = operation_date
        self._prepare_invoice_for_verifactu(invoice)

        res_dict = invoice._get_verifactu_invoice_dict_out()
        inv_dict = res_dict["RegistroAlta"]

        self.assertIn("FechaOperacion", inv_dict)
        self.assertEqual(
            inv_dict["FechaOperacion"], operation_date.strftime("%d-%m-%Y")
        )

    def test_operation_date_not_in_dict_when_equal(self):
        """Test that FechaOperacion is NOT included when date == invoice_date."""
        self._activate_certificate(self.certificate_password)
        invoice = self._create_test_invoice()
        invoice.date = invoice.invoice_date
        self._prepare_invoice_for_verifactu(invoice)

        res_dict = invoice._get_verifactu_invoice_dict_out()
        inv_dict = res_dict["RegistroAlta"]

        self.assertNotIn("FechaOperacion", inv_dict)

    def test_operation_date_refund(self):
        """Test that FechaOperacion works correctly with refund invoices."""
        self._activate_certificate(self.certificate_password)
        invoice = self._create_test_invoice()
        invoice.action_post()

        # Create refund with different operation date
        refund_wizard = (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=invoice.ids)
            .create(
                {
                    "date": invoice.invoice_date,
                    "reason": "Test refund",
                    "journal_id": invoice.journal_id.id,
                }
            )
        )
        refund_action = refund_wizard.reverse_moves()
        refund = self.env["account.move"].browse(refund_action["res_id"])

        # Set operation date different from invoice date
        operation_date = refund.invoice_date - timedelta(days=2)
        refund.date = operation_date
        self._prepare_invoice_for_verifactu(refund)

        res_dict = refund._get_verifactu_invoice_dict_out()
        inv_dict = res_dict["RegistroAlta"]

        self.assertIn("FechaOperacion", inv_dict)
        self.assertEqual(
            inv_dict["FechaOperacion"], operation_date.strftime("%d-%m-%Y")
        )
