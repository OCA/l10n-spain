# Copyright 2025 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from unittest.mock import patch

from odoo.exceptions import UserError, ValidationError

from .test_l10n_es_aeat_sii_invoice_summary_common import (
    TestL10nEsAeatSiiSummaryCommon,
)


class TestL10nEsAeatSiiSummary(TestL10nEsAeatSiiSummaryCommon):
    def test_aeat_check_exceptions_case_supplier_summary(self):
        with self.assertRaises(UserError):
            self.invoice_supplier_summary._aeat_check_exceptions()

    def test_aeat_check_exceptions_case_summary_vat(self):
        partner = self.env["res.partner"].create({"name": "Test partner"})
        invoice = self.env["account.move"].create(
            {
                "partner_id": partner.id,
                "invoice_date": "2018-02-01",
                "move_type": "out_invoice",
                "is_invoice_summary": True,
                "sii_invoice_summary_start": 1,
                "sii_invoice_summary_end": 10,
            }
        )
        invoice._aeat_check_exceptions()
        invoice.aeat_state = "sent"
        with self.assertRaises(UserError):
            invoice.write({"sii_invoice_summary_start": 2})
        with self.assertRaises(UserError):
            invoice.write({"sii_invoice_summary_end": 20})

    def test_valid_sii_dates(self):
        self.invoice_summary.sii_start_date = self.date_order_today
        self.invoice_summary.sii_end_date = False
        with self.assertRaises(ValidationError) as context_error:
            self.invoice_summary._valid_sii_dates()
        self.assertEqual(
            str(context_error.exception), "Select the start date and end date."
        )

        self.invoice_summary.sii_start_date = False
        self.invoice_summary.sii_end_date = self.date_order_today_2_months
        with self.assertRaises(ValidationError) as context_error:
            self.invoice_summary._valid_sii_dates()
        self.assertEqual(
            str(context_error.exception), "Select the start date and end date."
        )

        self.invoice_summary.sii_start_date = self.date_order_today
        self.invoice_summary.sii_end_date = self.date_order_today_min_2_days
        with self.assertRaises(ValidationError) as context_error:
            self.invoice_summary._valid_sii_dates()
        self.assertEqual(
            str(context_error.exception), "Start date must be before end date."
        )

    def test_check_sii_invoice_summary(self):
        self.invoice_summary.sii_invoice_summary_end = False
        with self.assertRaises(ValidationError) as context_error:
            self.invoice_summary._check_sii_summary()
        self.assertEqual(
            str(context_error.exception),
            "The First invoice and Last invoice fields cannot be empty.",
        )

    def test_populate_invoice_summary_by_dates(self):
        self.invoice_summary.sii_start_date = self.date_order_today
        self.invoice_summary.sii_end_date = self.date_order_today_2_months
        with patch.object(type(self.invoice_summary), "_valid_sii_dates"), patch.object(
            type(self.invoice_summary), "_populate_invoice_summary_by_dates"
        ) as mock_method:
            self.invoice_summary.populate_invoice_summary_by_dates()
            mock_method.assert_called_once()

        with patch.object(
            type(self.invoice_summary), "set_order_summary"
        ) as mock_method:
            self.invoice_summary._populate_invoice_summary_by_dates()
            mock_method.assert_called_once()
            invoice_line_id = self.invoice_summary.invoice_line_ids.filtered(
                lambda x: "{}-{}".format(
                    self.invoice_summary.sii_invoice_summary_start,
                    self.invoice_summary.sii_invoice_summary_end,
                )
            )
            sii_invoice_summary_start = invoice_line_id.name.split("-")[0]
            sii_invoice_summary_end = invoice_line_id.name.split("-")[-1]

            self.assertEqual(
                self.invoice_summary.sii_invoice_summary_start,
                sii_invoice_summary_start,
            )

            self.assertEqual(
                self.invoice_summary.sii_invoice_summary_end,
                sii_invoice_summary_end,
            )
            self.assertEqual(len([invoice_line_id.id]), 1)
            self.assertEqual(
                invoice_line_id.name,
                f"{sii_invoice_summary_start}-{sii_invoice_summary_end}",
            )

            pos_orders = self.PosOrder.search_read(
                [("invoice_summary_id", "=", self.invoice_summary.id)],
                ["amount_total"],
            )
            amount_total = sum([pos_order["amount_total"] for pos_order in pos_orders])
            self.assertEqual(
                invoice_line_id.price_unit,
                round(amount_total, 2),
            )

    def test_action_pos_order_summary(self):
        result = self.invoice_summary.action_pos_order_summary()
        self.assertEqual(result["type"], "ir.actions.act_window")
        self.assertEqual(result["res_model"], "pos.order")
