# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError

from .common import TestL10nEsSigausCommon


class TestL10nEsSigausInvoice(TestL10nEsSigausCommon):
    def create_invoice(self, date, lines, sigaus_no=False):
        invoice_lines = []
        for line in lines:
            invoice_lines.append(
                (
                    0,
                    False,
                    {
                        "product_id": line["product"].id,
                        "quantity": line["quantity"],
                        "price_unit": line["price_unit"],
                    },
                )
            )
        invoice = self.env["account.move"].create(
            {
                "company_id": self.company.id,
                "partner_id": self.partner.id,
                "invoice_date": date,
                "invoice_line_ids": invoice_lines,
                "move_type": "out_invoice",
                "is_sigaus": not sigaus_no,
            }
        )
        return invoice

    def create_reversal(self, reversal_type):
        lines = [
            {
                "product": self.product_sigaus_in_product,
                "quantity": 1.0,
                "price_unit": 2,
            },
            {
                "product": self.product_sigaus_in_category,
                "quantity": 2.0,
                "price_unit": 3,
            },
            {
                "product": self.product_sigaus_in_category_excluded,
                "quantity": 3.0,
                "price_unit": 4,
            },
        ]
        invoice = self.create_invoice("2023-01-01", lines)
        invoice.action_post()
        move_reversal = (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=[invoice.id])
            .create(
                {
                    "date": "2023-01-01",
                    "refund_method": reversal_type,
                    "journal_id": invoice.journal_id.id,
                }
            )
        )
        return invoice, move_reversal.reverse_moves()

    def test_invoice_without_sigaus_products(self):
        lines = [{"product": self.product_sigaus_no, "quantity": 2.0, "price_unit": 1}]
        invoice = self.create_invoice("2023-01-01", lines)
        self.assertEqual(invoice.sigaus_has_line, False)
        self.assertEqual(invoice.amount_untaxed, 2)

    def test_invoice_with_sigaus_products_no_weight(self):
        lines = [
            {"product": self.product_sigaus_no_weight, "quantity": 2.0, "price_unit": 1}
        ]
        invoice = self.create_invoice("2023-01-01", lines)
        self.assertEqual(invoice.sigaus_company, True)
        self.assertTrue(invoice.sigaus_automated_exception_id)

    def test_invoice_with_sigaus(self):
        lines = [
            {
                "product": self.product_sigaus_in_product,
                "quantity": 1.0,
                "price_unit": 2,
            },
            {
                "product": self.product_sigaus_in_category,
                "quantity": 2.0,
                "price_unit": 3,
            },
            {
                "product": self.product_sigaus_in_category_excluded,
                "quantity": 3.0,
                "price_unit": 4,
            },
        ]
        invoice = self.create_invoice("2023-01-01", lines, True)
        self.assertEqual(invoice.sigaus_has_line, False)
        self.assertEqual(invoice.amount_untaxed, 20.00)
        product_sigaus_in_product_line = invoice.invoice_line_ids.filtered(
            lambda a: a.product_id == self.product_sigaus_in_product
        )
        self.assertEqual(product_sigaus_in_product_line.sigaus_amount, 0.06)
        product_sigaus_in_category_line = invoice.invoice_line_ids.filtered(
            lambda a: a.product_id == self.product_sigaus_in_category
        )
        self.assertEqual(product_sigaus_in_category_line.sigaus_amount, 0.24)
        product_sigaus_in_product_line = invoice.invoice_line_ids.filtered(
            lambda a: a.product_id == self.product_sigaus_in_product
        )
        self.assertEqual(product_sigaus_in_product_line.sigaus_amount, 0.06)
        product_sigaus_in_category_excluded_line = invoice.invoice_line_ids.filtered(
            lambda a: a.product_id == self.product_sigaus_in_category_excluded
        )
        self.assertEqual(product_sigaus_in_category_excluded_line.sigaus_amount, 0.00)

        invoice.write({"is_sigaus": True})
        self.assertEqual(invoice.sigaus_has_line, True)
        self.assertEqual(invoice.amount_untaxed, 20.3)
        invoice.write(
            {
                "invoice_line_ids": [
                    (
                        0,
                        False,
                        {
                            "product_id": self.product_sigaus_in_product.id,
                            "quantity": 1.0,
                            "price_unit": 2,
                        },
                    )
                ]
            }
        )
        self.assertEqual(invoice.amount_untaxed, 22.36)
        invoice.write({"fiscal_position_id": self.fiscal_position_no_sigaus.id})
        self.assertEqual(invoice.amount_untaxed, 22.00)
        invoice.write({"fiscal_position_id": False})
        self.assertEqual(invoice.amount_untaxed, 22.36)
        invoice.write({"is_sigaus": False})
        self.assertEqual(invoice.amount_untaxed, 22.00)

    def test_invoice_with_sigaus_general_reverse(self):
        lines = [
            {
                "product": self.product_sigaus_in_product,
                "quantity": 1.0,
                "price_unit": 2,
            },
            {
                "product": self.product_sigaus_in_category,
                "quantity": 2.0,
                "price_unit": 3,
            },
            {
                "product": self.product_sigaus_in_category_excluded,
                "quantity": 3.0,
                "price_unit": 4,
            },
        ]
        invoice = self.create_invoice("2023-01-01", lines)
        invoice_sigaus_line = invoice.invoice_line_ids.filtered("is_sigaus")
        invoice.action_post()
        credit_note = invoice._reverse_moves()
        credit_note.write({"invoice_date": invoice.invoice_date})
        self.assertEqual(credit_note.move_type, "out_refund")
        self.assertEqual(invoice.amount_untaxed, credit_note.amount_untaxed)
        self.assertTrue(credit_note.is_sigaus)
        credit_note_sigaus_line = credit_note.invoice_line_ids.filtered("is_sigaus")
        self.assertEqual(len(credit_note_sigaus_line), 1)
        self.assertEqual(
            invoice_sigaus_line.price_subtotal, credit_note_sigaus_line.price_subtotal
        )

    def test_invoice_with_sigaus_reverse_refund(self):
        invoice, reversal = self.create_reversal("refund")
        invoice_sigaus_line = invoice.invoice_line_ids.filtered("is_sigaus")
        credit_note = self.env["account.move"].browse(reversal["res_id"])
        self.assertEqual(credit_note.move_type, "out_refund")
        self.assertEqual(invoice.amount_untaxed, credit_note.amount_untaxed)
        self.assertTrue(credit_note.is_sigaus)
        credit_note_sigaus_line = credit_note.invoice_line_ids.filtered("is_sigaus")
        self.assertEqual(len(credit_note_sigaus_line), 1)
        self.assertEqual(
            invoice_sigaus_line.price_subtotal, credit_note_sigaus_line.price_subtotal
        )
        self.assertEqual(
            invoice_sigaus_line.amount_currency,
            -1 * credit_note_sigaus_line.amount_currency,
        )

    def test_invoice_with_sigaus_reverse_cancel(self):
        invoice, reversal = self.create_reversal("cancel")
        invoice_sigaus_line = invoice.invoice_line_ids.filtered("is_sigaus")
        self.assertEqual(invoice.payment_state, "reversed")
        credit_note = self.env["account.move"].browse(reversal["res_id"])
        self.assertEqual(credit_note.move_type, "out_refund")
        self.assertEqual(invoice.amount_untaxed, credit_note.amount_untaxed)
        self.assertTrue(credit_note.is_sigaus)
        credit_note_sigaus_line = credit_note.invoice_line_ids.filtered("is_sigaus")
        self.assertEqual(len(credit_note_sigaus_line), 1)
        self.assertEqual(
            invoice_sigaus_line.price_subtotal, credit_note_sigaus_line.price_subtotal
        )
        self.assertEqual(
            invoice_sigaus_line.amount_currency,
            -1 * credit_note_sigaus_line.amount_currency,
        )

    def test_invoice_with_sigaus_reverse_modify(self):
        invoice, reversal = self.create_reversal("modify")
        invoice_sigaus_line = invoice.invoice_line_ids.filtered("is_sigaus")
        self.assertEqual(invoice.payment_state, "reversed")
        new_invoice = self.env["account.move"].browse(reversal["res_id"])
        new_invoice.write({"invoice_date": invoice.invoice_date})
        self.assertEqual(new_invoice.move_type, "out_invoice")
        self.assertEqual(invoice.amount_untaxed, new_invoice.amount_untaxed)
        self.assertTrue(new_invoice.is_sigaus)
        new_invoice_sigaus_line = new_invoice.invoice_line_ids.filtered("is_sigaus")
        self.assertEqual(len(new_invoice_sigaus_line), 1)
        self.assertEqual(
            invoice_sigaus_line.price_subtotal, new_invoice_sigaus_line.price_subtotal
        )
        self.assertEqual(
            invoice_sigaus_line.amount_currency, new_invoice_sigaus_line.amount_currency
        )

    def test_invoice_with_sigaus_different_dates(self):
        self.company.write({"sigaus_date_from": "3000-01-01"})
        lines = [
            {
                "product": self.product_sigaus_in_product,
                "quantity": 1.0,
                "price_unit": 2,
            },
            {
                "product": self.product_sigaus_in_category,
                "quantity": 2.0,
                "price_unit": 3,
            },
            {
                "product": self.product_sigaus_in_category_excluded,
                "quantity": 3.0,
                "price_unit": 4,
            },
        ]
        invoice = self.create_invoice(False, lines)
        self.assertFalse(invoice.sigaus_is_date)
        self.assertFalse(invoice.sigaus_has_line)
        invoice.write({"invoice_date": "3000-01-01"})
        self.assertTrue(invoice.sigaus_is_date)
        self.assertTrue(invoice.sigaus_has_line)
        self.company.write({"sigaus_date_from": "2023-01-01"})
        lines = [
            {
                "product": self.product_sigaus_in_product,
                "quantity": 1.0,
                "price_unit": 2,
            },
            {
                "product": self.product_sigaus_in_category,
                "quantity": 2.0,
                "price_unit": 3,
            },
            {
                "product": self.product_sigaus_in_category_excluded,
                "quantity": 3.0,
                "price_unit": 4,
            },
        ]
        invoice = self.create_invoice(False, lines)
        self.assertTrue(invoice.sigaus_is_date)
        self.assertTrue(invoice.sigaus_has_line)

    def test_copy_sigaus_invoice(self):
        lines = [
            {
                "product": self.product_sigaus_in_product,
                "quantity": 1.0,
                "price_unit": 2,
            },
            {
                "product": self.product_sigaus_in_category,
                "quantity": 2.0,
                "price_unit": 3,
            },
            {
                "product": self.product_sigaus_in_category_excluded,
                "quantity": 3.0,
                "price_unit": 4,
            },
        ]
        invoice = self.create_invoice("2023-01-01", lines)
        invoice_copy = invoice.copy({"invoice_date": "2023-01-01"})
        self.assertEqual(invoice.amount_untaxed, invoice_copy.amount_untaxed)
        self.assertTrue(invoice_copy.is_sigaus)
        self.assertTrue(invoice_copy.sigaus_has_line)
        self.assertEqual(len(invoice_copy.invoice_line_ids.filtered("is_sigaus")), 1)
        self.assertEqual(
            invoice_copy.invoice_line_ids.filtered("is_sigaus").price_subtotal, 0.3
        )
        invoice.write(
            {
                "invoice_line_ids": [
                    (
                        0,
                        False,
                        {
                            "product_id": self.product_sigaus_in_category.id,
                            "quantity": 2.0,
                            "price_unit": 3,
                        },
                    ),
                ]
            }
        )
        self.assertEqual(len(invoice_copy.invoice_line_ids.filtered("is_sigaus")), 1)
        self.assertEqual(
            invoice_copy.invoice_line_ids.filtered("is_sigaus").price_subtotal, 0.3
        )

    def test_invoice_error_date(self):
        lines = [
            {
                "product": self.product_sigaus_in_product,
                "quantity": 1.0,
                "price_unit": 2,
            }
        ]
        with self.assertRaises(ValidationError):
            self.create_invoice("2022-01-01", lines)
