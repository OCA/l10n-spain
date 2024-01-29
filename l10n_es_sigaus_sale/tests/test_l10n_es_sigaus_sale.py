# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError

from odoo.addons.l10n_es_sigaus_account.tests.common import TestL10nEsSigausCommon


class TestL10nEsSigausSales(TestL10nEsSigausCommon):
    def create_sale_order(self, date, fiscal_position, lines, sigaus_no=False):
        order_lines = []
        for line in lines:
            order_lines.append(
                (
                    0,
                    False,
                    {
                        "product_id": line["product"].id,
                        "product_uom_qty": line["quantity"],
                        "price_unit": line["price_unit"],
                    },
                )
            )
        vals = {
            "company_id": self.company.id,
            "partner_id": self.partner.id,
            "date_order": date,
            "fiscal_position_id": fiscal_position.id,
            "order_line": order_lines,
        }
        if sigaus_no:
            vals["is_sigaus"] = False
        return self.env["sale.order"].create(vals)

    def test_sale_without_sigaus_products(self):
        lines = [{"product": self.product_sigaus_no, "quantity": 2.0, "price_unit": 1}]
        sale = self.create_sale_order("2023-01-01", self.fiscal_position_sigaus, lines)
        self.assertEqual(sale.sigaus_company, True)
        self.assertEqual(sale.sigaus_has_line, False)
        self.assertEqual(sale.amount_untaxed, 2)

    def test_sale_with_sigaus_products_no_weight(self):
        lines = [
            {"product": self.product_sigaus_no_weight, "quantity": 2.0, "price_unit": 1}
        ]
        sale = self.create_sale_order("2023-01-01", self.fiscal_position_sigaus, lines)
        self.assertTrue(sale.is_sigaus)
        self.assertTrue(sale.sigaus_automated_exception_id)

    def test_sale_with_sigaus(self):
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
        sale = self.create_sale_order(
            "2023-01-01", self.fiscal_position_sigaus, lines, True
        )
        self.assertFalse(sale.is_sigaus)
        self.assertFalse(sale.sigaus_has_line)
        self.assertEqual(sale.amount_untaxed, 20.00)
        product_sigaus_in_product_line = sale.order_line.filtered(
            lambda a: a.product_id == self.product_sigaus_in_product
        )
        self.assertEqual(product_sigaus_in_product_line.sigaus_amount, 0.06)
        product_sigaus_in_category_line = sale.order_line.filtered(
            lambda a: a.product_id == self.product_sigaus_in_category
        )
        self.assertEqual(product_sigaus_in_category_line.sigaus_amount, 0.24)
        product_sigaus_in_product_line = sale.order_line.filtered(
            lambda a: a.product_id == self.product_sigaus_in_product
        )
        self.assertEqual(product_sigaus_in_product_line.sigaus_amount, 0.06)
        product_sigaus_in_category_excluded_line = sale.order_line.filtered(
            lambda a: a.product_id == self.product_sigaus_in_category_excluded
        )
        self.assertEqual(product_sigaus_in_category_excluded_line.sigaus_amount, 0.00)

        sale.write({"is_sigaus": True})
        self.assertTrue(sale.is_sigaus)
        self.assertTrue(sale.sigaus_has_line)
        self.assertEqual(sale.amount_untaxed, 20.3)
        sale.write(
            {
                "order_line": [
                    (
                        0,
                        False,
                        {
                            "product_id": self.product_sigaus_in_product.id,
                            "product_uom_qty": 1.0,
                            "price_unit": 2,
                        },
                    )
                ]
            }
        )
        self.assertTrue(sale.is_sigaus)
        self.assertEqual(sale.amount_untaxed, 22.36)
        sale.write({"fiscal_position_id": self.fiscal_position_no_sigaus.id})
        self.assertEqual(sale.amount_untaxed, 22.00)

    def test_invoice_from_single_sale(self):
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
        sale = self.create_sale_order("2023-01-01", self.fiscal_position_sigaus, lines)
        sale.action_done()
        invoice = sale._create_invoices()
        self.assertTrue(invoice.sigaus_has_line)
        self.assertEqual(invoice.amount_untaxed, 20.3)
        invoice.write({"invoice_date": "2023-01-01"})

        # Delete SIGAUS line from invoice a recreate it.
        # It needs to be related to the SIGAUS line in the sale order.
        invoice.invoice_line_ids.filtered("is_sigaus").unlink()
        sigaus_line_in_order = sale.order_line.filtered("is_sigaus")
        sigaus_line_in_invoice = invoice.invoice_line_ids.filtered("is_sigaus")
        self.assertEqual(sigaus_line_in_order, sigaus_line_in_invoice.sale_line_ids)

        invoice_copy = invoice.copy()
        self.assertTrue(invoice_copy.is_sigaus)
        self.assertTrue(invoice_copy.sigaus_has_line)
        self.assertEqual(len(invoice_copy.invoice_line_ids.filtered("is_sigaus")), 1)
        invoice_copy.write(
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
        self.assertEqual(len(invoice_copy.invoice_line_ids.filtered("is_sigaus")), 1)

    def test_invoice_from_multiple_sales(self):
        lines_1 = [
            {
                "product": self.product_sigaus_in_product,
                "quantity": 1.0,
                "price_unit": 2,
            }
        ]
        sale_1 = self.create_sale_order(
            "2023-01-01", self.fiscal_position_sigaus, lines_1
        )
        lines_2 = [
            {
                "product": self.product_sigaus_in_category,
                "quantity": 2.0,
                "price_unit": 3,
            }
        ]
        sale_2 = self.create_sale_order(
            "2023-01-01", self.fiscal_position_sigaus, lines_2
        )
        sale_1_sigaus_line = sale_1.order_line.filtered("is_sigaus")
        sale_1.action_done()
        sale_2_sigaus_line = sale_2.order_line.filtered("is_sigaus")
        sale_2.action_done()
        invoice = (sale_1 + sale_2)._create_invoices()
        sigaus_lines = invoice.invoice_line_ids.filtered("is_sigaus")
        self.assertEqual(len(sigaus_lines), 2)
        invoice_sale_1_sigaus_line = invoice.invoice_line_ids.filtered(
            lambda a: a.sale_line_ids == sale_1_sigaus_line
        )
        self.assertTrue(invoice_sale_1_sigaus_line)
        invoice_sale_2_sigaus_line = invoice.invoice_line_ids.filtered(
            lambda a: a.sale_line_ids == sale_2_sigaus_line
        )
        self.assertTrue(invoice_sale_2_sigaus_line)

        # Delete and regenerate one of the SIGAUS lines in invoice
        invoice_sale_1_sigaus_line.unlink()
        sigaus_lines = invoice.invoice_line_ids.filtered("is_sigaus")
        self.assertEqual(len(sigaus_lines), 2)
        invoice_sale_1_sigaus_line = invoice.invoice_line_ids.filtered(
            lambda a: a.sale_line_ids == sale_1_sigaus_line
        )
        self.assertTrue(
            invoice_sale_1_sigaus_line.price_subtotal, sale_1_sigaus_line.price_subtotal
        )
        self.assertTrue(invoice_sale_1_sigaus_line)
        invoice_sale_2_sigaus_line = invoice.invoice_line_ids.filtered(
            lambda a: a.sale_line_ids == sale_2_sigaus_line
        )
        self.assertTrue(
            invoice_sale_2_sigaus_line.price_subtotal, sale_2_sigaus_line.price_subtotal
        )
        self.assertTrue(invoice_sale_2_sigaus_line)

        invoice_copy = invoice.copy()
        self.assertTrue(invoice_copy.is_sigaus)
        self.assertTrue(invoice_copy.sigaus_has_line)
        self.assertEqual(len(invoice_copy.invoice_line_ids.filtered("is_sigaus")), 1)
        invoice_copy.write(
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
        self.assertEqual(len(invoice_copy.invoice_line_ids.filtered("is_sigaus")), 1)

    def test_sigaus_sale_copy(self):
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
        sale = self.create_sale_order("2023-01-01", self.fiscal_position_sigaus, lines)
        sale_copy = sale.copy({"date_order": sale.date_order})
        self.assertEqual(sale.amount_untaxed, sale_copy.amount_untaxed)
        self.assertTrue(sale_copy.is_sigaus)
        self.assertTrue(sale_copy.sigaus_has_line)
        self.assertEqual(len(sale_copy.order_line.filtered("is_sigaus")), 1)
        self.assertEqual(sale_copy.order_line.filtered("is_sigaus").price_subtotal, 0.3)

    def test_cancel_sale(self):
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
        sale = self.create_sale_order("2023-01-01", self.fiscal_position_sigaus, lines)
        sale.action_done()
        sale._create_invoices()
        sigaus_line = sale.order_line.filtered(lambda a: a.is_sigaus)
        sigaus_invoice_line = sigaus_line.invoice_lines
        self.assertTrue(sigaus_invoice_line)
        sale._action_cancel()
        self.assertEqual(sale.state, "cancel")
        sale.action_draft()
        self.assertEqual(sale.state, "draft")
        sigaus_line = sale.order_line.filtered(lambda a: a.is_sigaus)
        self.assertEqual(sigaus_line.invoice_lines, sigaus_invoice_line)

    def test_sale_error_date(self):
        lines = [
            {
                "product": self.product_sigaus_in_product,
                "quantity": 1.0,
                "price_unit": 2,
            }
        ]
        with self.assertRaises(ValidationError):
            self.create_sale_order("2022-01-06", self.fiscal_position_sigaus, lines)
