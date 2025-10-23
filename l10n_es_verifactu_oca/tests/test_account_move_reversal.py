# Copyright 2025 Process Control - Jorge Luis López
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from .common import TestVerifactuCommon


class TestAccountMoveReversal(TestVerifactuCommon):
    def test_reverse_moves_sets_refund_type(self):
        """Test that reversing moves sets correct VERI*FACTU refund type"""
        # Create and post invoice
        self.invoice.action_post()

        # Create reversal wizard
        reversal_wizard = (
            self.env["account.move.reversal"]
            .with_context(
                {
                    "active_model": "account.move",
                    "active_ids": self.invoice.ids,
                }
            )
            .create(
                {
                    "reason": "Test reversal",
                    "refund_method": "refund",
                }
            )
        )

        # Execute reversal
        result = reversal_wizard.reverse_moves()

        # Get the credit note created
        credit_note = self.invoice.reversal_move_id
        self.assertTrue(credit_note)
        self.assertEqual(credit_note.move_type, "out_refund")
        self.assertEqual(credit_note.verifactu_refund_type, "I")

        # Verify result contains the correct action
        self.assertIn("res_id", result)

    def test_reverse_moves_only_affects_customer_invoices(self):
        """Test that reversal only affects customer invoices, not vendor bills"""
        # Create vendor bill
        vendor_bill = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.partner.id,
                "company_id": self.company.id,
                "invoice_date": "2024-01-01",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "quantity": 1,
                            "price_unit": 100,
                        },
                    )
                ],
            }
        )
        vendor_bill.action_post()

        # Create reversal wizard for vendor bill
        reversal_wizard = (
            self.env["account.move.reversal"]
            .with_context(
                {
                    "active_model": "account.move",
                    "active_ids": vendor_bill.ids,
                }
            )
            .create(
                {
                    "reason": "Test vendor bill reversal",
                    "refund_method": "refund",
                }
            )
        )

        # Execute reversal
        reversal_wizard.reverse_moves()

        # Vendor bill reversal should not have verifactu_refund_type set
        credit_note = vendor_bill.reversal_move_id
        self.assertTrue(credit_note)
        self.assertEqual(credit_note.move_type, "in_refund")
        # verifactu_refund_type should remain False for vendor bills
        self.assertFalse(credit_note.verifactu_refund_type)
