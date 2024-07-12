# Copyright 2022 ProcessControl david.ramia@processcontrol.es
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import exceptions

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

    def test_sii_check_exceptions_case_supplier_summary(self):
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
            invoice._sii_check_exceptions()

    def test_sii_check_exceptions_case_summary_vat(self):
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
        invoice._sii_check_exceptions()
        invoice.sii_state = "sent"
        with self.assertRaises(exceptions.UserError):
            invoice.write({"sii_invoice_summary_start": 2})
        with self.assertRaises(exceptions.UserError):
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
            (
                "out_invoice",
                [(100, ["s_iva0_sp_i"]), (200, ["s_iva0_ic"])],
                {
                    "is_invoice_summary": True,
                    "sii_invoice_summary_start": 1,
                    "sii_invoice_summary_end": 1,
                },
            ),
            (
                "out_refund",
                [(100, ["s_iva0_sp_i"]), (200, ["s_iva0_ic"])],
                {
                    "is_invoice_summary": True,
                    "sii_invoice_summary_start": 1,
                    "sii_invoice_summary_end": 1,
                },
            ),
            (
                "out_invoice",
                [(100, ["s_iva_e"]), (200, ["s_iva0_e"])],
                {
                    "is_invoice_summary": True,
                    "sii_invoice_summary_start": 1,
                    "sii_invoice_summary_end": 1,
                },
            ),
            (
                "out_refund",
                [(100, ["s_iva_e"]), (200, ["s_iva0_e"])],
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
            (
                "out_invoice",
                [(100, ["s_iva0_sp_i"]), (200, ["s_iva0_ic"])],
                {
                    "is_invoice_summary": True,
                    "sii_invoice_summary_start": 1,
                    "sii_invoice_summary_end": 10,
                },
            ),
            (
                "out_refund",
                [(100, ["s_iva0_sp_i"]), (200, ["s_iva0_ic"])],
                {
                    "is_invoice_summary": True,
                    "sii_invoice_summary_start": 1,
                    "sii_invoice_summary_end": 10,
                },
            ),
            (
                "out_invoice",
                [(100, ["s_iva_e"]), (200, ["s_iva0_e"])],
                {
                    "is_invoice_summary": True,
                    "sii_invoice_summary_start": 1,
                    "sii_invoice_summary_end": 10,
                },
            ),
            (
                "out_refund",
                [(100, ["s_iva_e"]), (200, ["s_iva0_e"])],
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
        return

    def _compare_sii_dict(
        self, json_file, inv_type, lines, extra_vals=None, module=None
    ):
        if extra_vals.get("sii_invoice_summary_start") and extra_vals.get(
            "sii_invoice_summary_start"
        ) == extra_vals.get("sii_invoice_summary_end"):
            json_file = json_file.replace("dict.json", "same_dict.json")
        return super()._compare_sii_dict(json_file, inv_type, lines, extra_vals, module)
