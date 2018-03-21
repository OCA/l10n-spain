# Copyright 2022 ProcessControl david.ramia@processcontrol.es
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

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

    def test_get_invoice_data_summary_case_same_number(self):
        mapping = [
            (
                "out_invoice",
                [(100, ["s_iva10b"]), (200, ["s_iva21s"])],
                {
                    "is_invoice_summary": True,
                    "sii_invoice_summary_start": 1,
                    "sii_invoice_summary_end": 1,
                },
            ),
            (
                "out_invoice",
                [(100, ["s_iva10b"]), (200, ["s_iva0_ns"])],
                {
                    "is_invoice_summary": True,
                    "sii_invoice_summary_start": 1,
                    "sii_invoice_summary_end": 1,
                },
            ),
            (
                "out_invoice",
                [(100, ["s_iva10b", "s_req014"]), (200, ["s_iva21s", "s_req52"])],
                {
                    "is_invoice_summary": True,
                    "sii_invoice_summary_start": 1,
                    "sii_invoice_summary_end": 1,
                },
            ),
            (
                "out_refund",
                [(100, ["s_iva10b"]), (100, ["s_iva10b"]), (200, ["s_iva21s"])],
                {
                    "is_invoice_summary": True,
                    "sii_invoice_summary_start": 1,
                    "sii_invoice_summary_end": 1,
                },
            ),
        ]
        for inv_type, lines, extra_vals in mapping:
            self._create_and_test_invoice_sii_dict(
                inv_type, lines, extra_vals, "l10n_es_aeat_sii_invoice_summary"
            )
        return

    def test_get_invoice_data_summary(self):
        mapping = [
            (
                "out_invoice",
                [(100, ["s_iva10b"]), (200, ["s_iva21s"])],
                {
                    "is_invoice_summary": True,
                    "sii_invoice_summary_start": 1,
                    "sii_invoice_summary_end": 10,
                },
            ),
            (
                "out_invoice",
                [(100, ["s_iva10b"]), (200, ["s_iva0_ns"])],
                {
                    "is_invoice_summary": True,
                    "sii_invoice_summary_start": 1,
                    "sii_invoice_summary_end": 10,
                },
            ),
            (
                "out_invoice",
                [(100, ["s_iva10b", "s_req014"]), (200, ["s_iva21s", "s_req52"])],
                {
                    "is_invoice_summary": True,
                    "sii_invoice_summary_start": 1,
                    "sii_invoice_summary_end": 10,
                },
            ),
            (
                "out_refund",
                [(100, ["s_iva10b"]), (100, ["s_iva10b"]), (200, ["s_iva21s"])],
                {
                    "is_invoice_summary": True,
                    "sii_invoice_summary_start": 1,
                    "sii_invoice_summary_end": 10,
                },
            ),
        ]
        for inv_type, lines, extra_vals in mapping:
            self._create_and_test_invoice_sii_dict(
                inv_type, lines, extra_vals, "l10n_es_aeat_sii_invoice_summary"
            )
        return

    def _compare_sii_dict(
        self, json_file, inv_type, lines, extra_vals=None, module=None
    ):
        if extra_vals.get("sii_invoice_summary_start") and extra_vals.get(
            "sii_invoice_summary_start"
        ) == extra_vals.get("sii_invoice_summary_end"):
            json_file = json_file.replace("dict.json", "same_dict.json")
        return super()._compare_sii_dict(json_file, inv_type, lines, extra_vals, module)

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

    def test_action_post(self):
        with patch.object(
            type(self.invoice_summary), "populate_invoice_summary_by_dates"
        ) as mock_method:
            self.invoice_summary.action_post()
            mock_method.assert_called_once()

    def test_populate_invoice_summary_by_dates(self):
        self.invoice_summary.sii_start_date = self.date_order_today
        self.invoice_summary.sii_end_date = self.date_order_today_2_months
        with patch.object(type(self.invoice_summary), "_valid_sii_dates"), patch.object(
            type(self.invoice_summary), "_populate_invoice_summary_by_dates"
        ) as mock_method:
            self.invoice_summary.populate_invoice_summary_by_dates()
            mock_method.assert_called_once()

        self.invoice_summary.sii_tickets = (
            f"{self.pos_order_1.name},{self.pos_order_2.name}"
        )
        with patch.object(
            type(self.invoice_summary), "set_order_presented"
        ) as mock_method:
            self.invoice_summary._populate_invoice_summary_by_dates()
            self.assertEqual(mock_method.call_count, 2)
            invoice_line_ids = self.invoice_summary.invoice_line_ids.filtered(
                lambda x: x.is_sii_line
            )
            sii_invoice_summary_start = invoice_line_ids.name.split("-")[0]
            sii_invoice_summary_end = invoice_line_ids.name.split("-")[-1]
            fields = ["id", "amount_total"]
            pos_order_1 = self.PosOrder.search_read(
                [("name", "=", sii_invoice_summary_start)], fields
            )
            pos_order_2 = self.PosOrder.search_read(
                [("name", "=", sii_invoice_summary_end)], fields
            )

            self.assertEqual(
                self.invoice_summary.sii_invoice_summary_start,
                sii_invoice_summary_start,
            )

            self.assertEqual(
                self.invoice_summary.sii_invoice_summary_end,
                sii_invoice_summary_end,
            )
            self.assertEqual(len(invoice_line_ids), 1)
            self.assertEqual(
                invoice_line_ids.name,
                f"{sii_invoice_summary_start}-{sii_invoice_summary_end}",
            )
            self.assertEqual(
                invoice_line_ids.price_unit,
                pos_order_1[0]["amount_total"] + pos_order_2[0]["amount_total"],
            )
            self.assertTrue(invoice_line_ids.is_sii_line)
