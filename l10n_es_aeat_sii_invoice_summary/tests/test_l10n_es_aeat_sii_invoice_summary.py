# Copyright 2022 ProcessControl david.ramia@processcontrol.es
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import exceptions
from odoo.tests import Form

from odoo.addons.l10n_es_aeat_sii_oca.tests.test_l10n_es_aeat_sii import (
    TestL10nEsAeatSiiBase,
)


class TestL10nEsAeatSiiSummary(TestL10nEsAeatSiiBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.invoice.is_invoice_summary = True
        cls.invoice.sii_invoice_summary_start = True
        cls.invoice.sii_invoice_summary_end = True

    def test_aeat_check_exceptions_case_supplier_summary(self):
        invoice = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "invoice_date": "2018-02-01",
                "move_type": "in_invoice",
                "is_invoice_summary": True,
                "sii_invoice_summary_start": 1,
                "sii_invoice_summary_end": 10,
            }
        )
        with self.assertRaises(exceptions.UserError):
            invoice._aeat_check_exceptions()

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
        with self.assertRaises(exceptions.UserError):
            invoice.write({"sii_invoice_summary_start": 2})
        with self.assertRaises(exceptions.UserError):
            invoice.write({"sii_invoice_summary_end": 20})

    def _summary(self, move_type="out_invoice", **vals):
        """Daily summary of the tickets of a point of sale, as the importers of
        another sales program create it: simplified type, range and lines."""
        partner = self.env["res.partner"].create({"name": "Clientes TPV"})
        return self.env["account.move"].create(
            {
                "partner_id": partner.id,
                "invoice_date": "2020-01-01",
                "move_type": move_type,
                "is_invoice_summary": True,
                "sii_invoice_summary_start": "T-0001",
                "sii_invoice_summary_end": "T-0250",
                "l10n_es_invoice_type": "R5" if move_type == "out_refund" else "F2",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "account_id": self.account_expense.id,
                            "name": "Daily sales",
                            "price_unit": 5000,
                            "quantity": 1,
                        },
                    )
                ],
                **vals,
            }
        )

    def _reverse(self, invoice):
        reversal = (
            self.env["account.move.reversal"]
            .with_context(active_model=invoice._name, active_ids=invoice.ids)
            .create({"journal_id": invoice.journal_id.id})
        )
        action = reversal.refund_moves()
        return self.env["account.move"].browse(action["res_id"])

    def test_summary_flow(self):
        """An imported daily summary becomes an F4 when posted, is sent with
        its range and without counterpart, its cancellation is identified by
        the same range, and its credit note is an R5 without range."""
        summary = self._summary()
        summary.action_post()
        self.assertEqual(summary.l10n_es_invoice_type, "F4")
        sii_info = summary._get_aeat_invoice_dict()
        self.assertEqual(sii_info["IDFactura"]["NumSerieFacturaEmisor"], "T-0001")
        self.assertEqual(
            sii_info["IDFactura"]["NumSerieFacturaEmisorResumenFin"], "T-0250"
        )
        self.assertEqual(sii_info["FacturaExpedida"]["TipoFactura"], "F4")
        self.assertNotIn("Contraparte", sii_info["FacturaExpedida"])
        cancel_info = summary._get_cancel_sii_invoice_dict()
        self.assertEqual(cancel_info["IDFactura"], sii_info["IDFactura"])
        refund = self._reverse(summary)
        self.assertEqual(refund.l10n_es_invoice_type, "R5")
        refund.action_post()
        sii_info = refund._get_aeat_invoice_dict()
        self.assertEqual(sii_info["IDFactura"]["NumSerieFacturaEmisor"], refund.name)
        self.assertNotIn("NumSerieFacturaEmisorResumenFin", sii_info["IDFactura"])
        self.assertEqual(sii_info["FacturaExpedida"]["TipoFactura"], "R5")
        self.assertNotIn("Contraparte", sii_info["FacturaExpedida"])

    def test_summary_form(self):
        """Marking an invoice as a summary on the form sets its type: F4 for
        a range, F2 when the first and the last invoice are the same one."""
        partner = self.env["res.partner"].create(
            {"name": "Customer", "vat": "ESA12345674"}
        )
        with Form(
            self.env["account.move"].with_context(default_move_type="out_invoice")
        ) as invoice_form:
            invoice_form.partner_id = partner
            invoice_form.invoice_date = "2020-01-01"
            with invoice_form.invoice_line_ids.new() as line_form:
                line_form.product_id = self.product
                line_form.price_unit = 5000
            self.assertEqual(invoice_form.l10n_es_invoice_type, "F1")
            invoice_form.is_invoice_summary = True
            invoice_form.sii_invoice_summary_start = "T-0001"
            invoice_form.sii_invoice_summary_end = "T-0250"
            self.assertEqual(invoice_form.l10n_es_invoice_type, "F4")
            invoice_form.sii_invoice_summary_end = "T-0001"
            self.assertEqual(invoice_form.l10n_es_invoice_type, "F2")

    def test_summary_type_without_range(self):
        """An F4 chosen by hand on an invoice that is not a summary cannot be
        posted: the AEAT needs the range."""
        invoice = self._summary(
            is_invoice_summary=False,
            sii_invoice_summary_start=False,
            sii_invoice_summary_end=False,
            l10n_es_invoice_type="F4",
        )
        with self.assertRaises(exceptions.UserError):
            invoice.action_post()

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
            (
                "out_invoice",
                [(100, ["s_iva0_sp_i"]), (200, ["s_iva0_g_i"])],
                {
                    "is_invoice_summary": True,
                    "sii_invoice_summary_start": 1,
                    "sii_invoice_summary_end": 1,
                },
            ),
            (
                "out_refund",
                [(100, ["s_iva0_sp_i"]), (200, ["s_iva0_g_i"])],
                {
                    "is_invoice_summary": True,
                    "sii_invoice_summary_start": 1,
                    "sii_invoice_summary_end": 1,
                },
            ),
            (
                "out_invoice",
                [(100, ["s_iva_e"]), (200, ["s_iva0_g_e"])],
                {
                    "is_invoice_summary": True,
                    "sii_invoice_summary_start": 1,
                    "sii_invoice_summary_end": 1,
                },
            ),
            (
                "out_refund",
                [(100, ["s_iva_e"]), (200, ["s_iva0_g_e"])],
                {
                    "is_invoice_summary": True,
                    "sii_invoice_summary_start": 1,
                    "sii_invoice_summary_end": 1,
                },
            ),
            # Out invoice with currency
            (
                "out_invoice",
                [(100, ["s_iva10b"])],
                {
                    "currency_id": self.usd.id,
                    "is_invoice_summary": True,
                    "sii_invoice_summary_start": 1,
                    "sii_invoice_summary_end": 1,
                },
            ),
            # Out invoice with currency and with not included in total amount
            (
                "out_invoice",
                [(100, ["s_iva10b", "s_irpf1"])],
                {
                    "currency_id": self.usd.id,
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
            (
                "out_invoice",
                [(100, ["s_iva0_sp_i"]), (200, ["s_iva0_g_i"])],
                {
                    "is_invoice_summary": True,
                    "sii_invoice_summary_start": 1,
                    "sii_invoice_summary_end": 10,
                    "fiscal_position_id": self.fp_intra.id,
                },
            ),
            (
                "out_refund",
                [(100, ["s_iva0_sp_i"]), (200, ["s_iva0_g_i"])],
                {
                    "is_invoice_summary": True,
                    "sii_invoice_summary_start": 1,
                    "sii_invoice_summary_end": 10,
                    "fiscal_position_id": self.fp_intra.id,
                },
            ),
            (
                "out_invoice",
                [(100, ["s_iva_e"]), (200, ["s_iva0_g_e"])],
                {
                    "is_invoice_summary": True,
                    "sii_invoice_summary_start": 1,
                    "sii_invoice_summary_end": 10,
                },
            ),
            (
                "out_refund",
                [(100, ["s_iva_e"]), (200, ["s_iva0_g_e"])],
                {
                    "is_invoice_summary": True,
                    "sii_invoice_summary_start": 1,
                    "sii_invoice_summary_end": 10,
                },
            ),
            # Out invoice with currency
            (
                "out_invoice",
                [(100, ["s_iva10b"])],
                {
                    "currency_id": self.usd.id,
                    "is_invoice_summary": True,
                    "sii_invoice_summary_start": 1,
                    "sii_invoice_summary_end": 10,
                },
            ),
            # Out invoice with currency and with not included in total amount
            (
                "out_invoice",
                [(100, ["s_iva10b", "s_irpf1"])],
                {
                    "currency_id": self.usd.id,
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

    def _compare_sii_dict(
        self, json_file, inv_type, lines, extra_vals=None, module=None
    ):
        if extra_vals.get("sii_invoice_summary_start") and extra_vals.get(
            "sii_invoice_summary_start"
        ) == extra_vals.get("sii_invoice_summary_end"):
            json_file = json_file.replace("dict.json", "same_dict.json")
        return super()._compare_sii_dict(json_file, inv_type, lines, extra_vals, module)
