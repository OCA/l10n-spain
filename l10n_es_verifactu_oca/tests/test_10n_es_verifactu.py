# Copyright 2024 Aures TIC - Almudena de La Puente
# Copyright 2024 FactorLibre - Luis J. Salvatierra
# Copyright 2025 ForgeFlow S.L.
# Copyright 2025 Process Control - Jorge Luis López
# Copyright 2025 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
import json
from datetime import datetime, timedelta
from hashlib import sha256
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

from freezegun import freeze_time

from odoo import Command, _, fields
from odoo.exceptions import UserError
from odoo.modules.module import get_resource_path

from .common import TestVerifactuCommon


class TestL10nEsAeatVerifactu(TestVerifactuCommon):
    def test_verifactu_hash_code(self):
        # based on AEAT VERI*FACTU documentation
        # https://www.agenciatributaria.es/static_files/AEAT_Desarrolladores/EEDD/IVA/VERI-FACTU/Veri-Factu_especificaciones_huella_hash_registros.pdf  # noqa: B950
        expected_hash = (
            "6FA5B3FA912C71B23C274952AA00E13A5F40F0CEE466640FFAAD041FA8B79BFF"
        )
        verifactu_hash_string = (
            "IDEmisorFactura=89890001K&"
            "NumSerieFactura=12345678/G33&"
            "FechaExpedicionFactura=01-01-2026&"
            "TipoFactura=F1&"
            "CuotaTotal=12.35&"
            "ImporteTotal=123.45&"
            "Huella=&"
            "FechaHoraHusoGenRegistro=2026-01-01T19:20:30+01:00"
        )
        sha_hash_code = sha256(verifactu_hash_string.encode("utf-8"))
        hash_code = sha_hash_code.hexdigest().upper()
        self.assertEqual(hash_code, expected_hash)

    def _create_and_test_invoice_verifactu_dict(
        self, name, inv_type, lines, extra_vals, module=None
    ):
        vals = []
        tax_names = []
        for line in lines:
            taxes = self.env["account.tax"]
            for tax in line[1]:
                if "." in tax:
                    xml_id = tax
                else:
                    xml_id = "l10n_es.{}_account_tax_template_{}".format(
                        self.company.id, tax
                    )
                taxes += self.env.ref(xml_id)
                tax_names.append(tax)
            vals.append({"price_unit": line[0], "taxes": taxes})
        return self._compare_verifactu_dict(
            "verifactu_{}_{}_dict.json".format(inv_type, "_".join(tax_names)),
            name,
            inv_type,
            vals,
            extra_vals=extra_vals,
            module=module,
        )

    def _compare_verifactu_dict(
        self, json_file, name, inv_type, lines, extra_vals=None, module=None
    ):
        """Helper method for creating an invoice according arguments, and
        comparing the expected verifactu dict with .
        """
        module = module or "l10n_es_verifactu_oca"
        vals = {
            "name": name,
            "partner_id": self.partner.id,
            "invoice_date": "2026-01-01",
            "move_type": inv_type,
            "invoice_line_ids": [],
        }
        for line in lines:
            vals["invoice_line_ids"].append(
                Command.create(
                    {
                        "product_id": self.product.id,
                        "account_id": self.account_expense.id,
                        "name": "Test line",
                        "price_unit": line["price_unit"],
                        "quantity": 1,
                        "tax_ids": [(6, 0, line["taxes"].ids)],
                    },
                )
            )
        if extra_vals:
            vals.update(extra_vals)
        invoice = self.env["account.move"].create(vals)
        self._activate_certificate(self.certificate_password)
        first_now = datetime(2026, 1, 1, 19, 20, 30)
        with patch.object(self.env.cr, "now", lambda: first_now), freeze_time(
            first_now
        ):
            invoice.action_post()
        result_dict = invoice._get_verifactu_invoice_dict()
        result_dict["RegistroAlta"].pop("FechaHoraHusoGenRegistro")
        result_dict["RegistroAlta"].pop("TipoHuella")
        result_dict["RegistroAlta"].pop("Huella")
        path = get_resource_path(module, "tests/json", json_file)
        if not path:
            raise Exception("Incorrect JSON file: %s" % json_file)
        with open(path, "r") as f:
            expected_dict = json.loads(f.read())
        self.assertEqual(expected_dict, result_dict)
        entry = invoice.last_verifactu_invoice_entry_id
        # Verify integration workflow
        self.assertTrue(entry, "Invoice should have verifactu entry")
        self.assertTrue(entry.aeat_json_data, "Should have JSON data")
        return invoice

    def test_get_verifactu_invoice_data(self):
        mapping = [
            (
                "TEST001",
                "out_invoice",
                [(100, ["s_iva10b"]), (200, ["s_iva21s"])],
                {
                    "fiscal_position_id": self.fp_nacional.id,
                    "verifactu_registration_key": self.fp_registration_key_01.id,
                    "verifactu_registration_date": "2026-01-01 19:20:30",
                },
            ),
            (
                "TEST002",
                "out_refund",
                [(100, ["s_iva10b"]), (100, ["s_iva10b"]), (200, ["s_iva21s"])],
                {
                    "fiscal_position_id": self.fp_nacional.id,
                    "verifactu_registration_key": self.fp_registration_key_01.id,
                    "verifactu_registration_date": "2026-01-01 19:20:30",
                },
            ),
            (
                "TEST003",
                "out_invoice",
                [(200, ["s_iva21s", "s_req52"])],
                {
                    "fiscal_position_id": self.fp_recargo.id,
                    "verifactu_registration_key": self.fp_registration_key_01.id,
                    "verifactu_registration_date": "2026-01-01 19:20:30",
                },
            ),
        ]
        for name, inv_type, lines, extra_vals in mapping:
            self._create_and_test_invoice_verifactu_dict(
                name, inv_type, lines, extra_vals
            )
        return

    def test_verifactu_start_date(self):
        self.company.verifactu_start_date = "2018-01-01"
        invoice1 = self.invoice.copy({"invoice_date": "2019-01-01"})
        self.assertTrue(invoice1.verifactu_enabled)
        invoice2 = self.invoice.copy({"invoice_date": "2017-01-01"})
        invoice2.invoice_date = "2017-01-01"
        self.assertFalse(invoice2.verifactu_enabled)
        self.company.verifactu_start_date = False
        self.assertTrue(invoice2.verifactu_enabled)

    def test_verifactu_export_invoice_data(self):
        mapping = [
            (
                "TEST_EXPORT",
                "out_invoice",
                [(200, ["s_iva_ns"])],
                {
                    "fiscal_position_id": self.fp_extra.id,
                    "verifactu_registration_key": self.fp_registration_key_02.id,
                    "verifactu_registration_date": "2026-01-01 19:20:30",
                },
            )
        ]
        for name, inv_type, lines, extra_vals in mapping:
            self._create_and_test_invoice_verifactu_dict(
                name, inv_type, lines, extra_vals
            )

    def test_verifactu_with_exemption_cause_e5_invoice_data(self):
        # test exemption cause E5
        mapping = [
            (
                "TEST_EXEMPT_001",
                "out_invoice",
                [(200, ["s_iva0_ic"])],
                {
                    "fiscal_position_id": self.fp_extra.id,
                    "verifactu_registration_key": self.fp_registration_key_02.id,
                    "verifactu_registration_date": "2026-01-01 19:20:30",
                },
            )
        ]
        for name, inv_type, lines, extra_vals in mapping:
            self._create_and_test_invoice_verifactu_dict(
                name, inv_type, lines, extra_vals
            )

    def test_verifactu_with_exemption_cause_e2_invoice_data(self):
        # test exemption cause E2
        mapping_2 = [
            (
                "TEST_EXEMPT_002",
                "out_invoice",
                [(200, ["s_iva0_e"])],
                {
                    "fiscal_position_id": self.fp_nacional.id,
                    "verifactu_registration_key": self.fp_registration_key_01.id,
                    "verifactu_registration_date": "2026-01-01 19:20:30",
                },
            )
        ]
        for name, inv_type, lines, extra_vals in mapping_2:
            self._create_and_test_invoice_verifactu_dict(
                name, inv_type, lines, extra_vals
            )
        return


class TestL10nEsAeatVerifactuQR(TestVerifactuCommon):
    def _get_required_qr_params(self):
        """Helper to generate the required QR code parameters."""
        return {
            "nif": self.invoice.company_id.partner_id._parse_aeat_vat_info()[2],
            "numserie": self.invoice.name,
            "fecha": self.invoice._get_verifactu_date(self.invoice.invoice_date),
            "importe": f"{self.invoice.amount_total:.2f}",  # noqa
        }

    def test_verifactu_qr_generation(self):
        """
        Test the generation of the QR code image for the invoice.
        """
        self._activate_certificate(self.certificate_password)
        self.invoice.action_post()
        qr_code = self.invoice.verifactu_qr
        self.assertTrue(qr_code, "QR code should be generated for the invoice.")
        self.assertIsInstance(qr_code, bytes, "QR code should be in bytes format.")

    def test_verifactu_qr_url_format(self):
        """
        Test the format of the generated QR URL to ensure it meets expected criteria.
        """
        self._activate_certificate(self.certificate_password)
        self.invoice.action_post()
        qr_url = self.invoice.verifactu_qr_url
        self.assertTrue(qr_url, "QR URL should be generated for the invoice.")
        test_url = self.env.ref(
            "l10n_es_aeat.aeat_tax_agency_spain"
        ).verifactu_qr_base_url_test_address
        self.assertTrue(test_url, "Test URL should not be empty.")
        parsed_url = urlparse(qr_url)
        actual_params = parse_qs(parsed_url.query)
        expected_params = self._get_required_qr_params()
        for key, expected_value in expected_params.items():
            self.assertIn(
                key, actual_params, f"QR URL should contain the parameter: {key}"
            )
            self.assertEqual(
                actual_params[key][0],
                str(expected_value),
                f"QR URL parameter '{key}' should have value '{expected_value}', "
                "got '{actual_params[key][0]}' instead.",
            )

    def test_verifactu_qr_code_generation_on_draft(self):
        """
        Ensure that the QR code is not generated for invoices in draft state.
        """
        qr_code = self.invoice.verifactu_qr
        self.assertFalse(qr_code, "QR code should not be generated for draft invoices.")

    def test_verifactu_qr_code_after_update(self):
        """
        Test that the QR code is regenerated if the invoice details are updated.
        """
        self._activate_certificate(self.certificate_password)
        self.invoice.action_post()
        original_qr_code = self.invoice.verifactu_qr
        with self.assertRaises(UserError):
            self.invoice.button_cancel()
            self.invoice.button_draft()
            self.invoice.write(
                {
                    "invoice_line_ids": [
                        Command.create(
                            {
                                "product_id": self.product.id,
                                "account_id": self.account_expense.id,
                                "name": "Updated line",
                                "price_unit": 200,
                                "quantity": 1,
                            },
                        )
                    ]
                }
            )
            self.invoice.action_post()
            self.invoice.invalidate_model(["verifactu_qr_url", "verifactu_qr"])
            updated_qr_code = self.invoice.verifactu_qr
            self.assertNotEqual(
                original_qr_code,
                updated_qr_code,
                "QR code should be regenerated after invoice update.",
            )

    def test_send_invoices_to_verifactu(self):
        self._activate_certificate(self.certificate_password)
        self.invoice.action_post()
        with patch(
            "odoo.addons.l10n_es_verifactu_oca.models."
            "verifactu_invoice_entry.VerifactuInvoiceEntry._connect_verifactu"
        ) as mock_connect:
            json_file = "verifactu_mocked_response_correct.json"
            self.mock_test(mock_connect, json_file)
            self.assertEqual(
                self.invoice.aeat_state,
                "sent",
                "Invoice should be marked as sent after VERI*FACTU processing.",
            )
            self.assertEqual(
                self.invoice.verifactu_csv,
                "A-Y23JP3582934",
                "CSV should be generated correctly after sending to VERI*FACTU.",
            )

    def mock_test(self, mock_connect, json_file):
        mock_service = MagicMock()
        module = "l10n_es_verifactu_oca"
        path = get_resource_path(module, "tests/json", json_file)
        if not path:
            raise Exception("Incorrect JSON file: %s" % json_file)
        with open(path, "r") as f:
            response_dict = json.loads(f.read())
        # Update the response to use the actual invoice name from the test
        if "RespuestaLinea" in response_dict and response_dict["RespuestaLinea"]:
            for line in response_dict["RespuestaLinea"]:
                if "IDFactura" in line and "NumSerieFactura" in line["IDFactura"]:
                    line["IDFactura"]["NumSerieFactura"] = self.invoice.name
        mock_service.RegFactuSistemaFacturacion.return_value = response_dict
        mock_connect.return_value = mock_service
        # Execute the cron job to send the invoice to VERI*FACTU
        self.env["verifactu.invoice.entry"]._cron_send_documents_to_verifactu()

    def test_send_invoices_to_verifactu_with_incorrect_response(self):
        self._activate_certificate(self.certificate_password)
        self.invoice.action_post()
        with patch(
            "odoo.addons.l10n_es_verifactu_oca.models."
            "verifactu_invoice_entry.VerifactuInvoiceEntry._connect_verifactu"
        ) as mock_connect:
            json_file = "verifactu_mocked_response_incorrect.json"
            self.mock_test(mock_connect, json_file)
            self.assertEqual(
                self.invoice.aeat_state,
                "incorrect",
                "Invoice should be marked as incorrect after VERI*FACTU processing.",
            )
            self.assertEqual(
                self.invoice.aeat_send_failed,
                True,
                "Invoice send be marked as failed after VERI*FACTU processing.",
            )

    def test_send_invoices_to_verifactu_duplicated(self):
        self._activate_certificate(self.certificate_password)
        self.invoice.action_post()
        with patch(
            "odoo.addons.l10n_es_verifactu_oca.models."
            "verifactu_invoice_entry.VerifactuInvoiceEntry._connect_verifactu"
        ) as mock_connect:
            json_file = "verifactu_mocked_response_correct.json"
            self.mock_test(mock_connect, json_file)
            self.assertEqual(
                self.invoice.aeat_state,
                "sent",
                "Invoice should be marked as sent after VERI*FACTU processing.",
            )
            # now we send the same invoice again
            # we need to truncate the aeat_state as if the previous response was incorrect
            # to force a new send a get the duplicated response
            self.invoice.aeat_state = "incorrect"
            self.invoice.resend_verifactu()
            json_file = "verifactu_mocked_response_duplicated.json"
            self.mock_test(mock_connect, json_file)
            self.assertEqual(
                self.invoice.aeat_state,
                "incorrect",
                "Invoice should be marked as incorrect after VERI*FACTU processing.",
            )

    def test_cancel_invoices_to_verifactu(self):
        self._activate_certificate(self.certificate_password)
        self.invoice.action_post()
        with patch(
            "odoo.addons.l10n_es_verifactu_oca.models."
            "verifactu_invoice_entry.VerifactuInvoiceEntry._connect_verifactu"
        ) as mock_connect:
            json_file = "verifactu_mocked_response_correct.json"
            self.mock_test(mock_connect, json_file)
            self.assertEqual(
                self.invoice.aeat_state,
                "sent",
                "Invoice should be marked as sent after VERI*FACTU processing.",
            )

            # now send the cancellation to verifactu with an incorrect cancellation response
            wiz = self.env["verifactu.cancel.invoice.wizard"].create(
                {"invoice_id": self.invoice.id, "cancel_reason": "Test Cancel Reason"}
            )
            wiz.cancel_invoice_in_verifactu()
            self.assertEqual(
                self.invoice.state, "cancel", "Invoice should be in cancel state"
            )
            self.assertEqual(
                self.invoice.verifactu_cancel_reason,
                "Test Cancel Reason",
                "Invoice cancel reason should be Test Cancel Reason",
            )
            json_file = "verifactu_mocked_response_cancel_incorrect.json"
            self.mock_test(mock_connect, json_file)
            self.assertEqual(
                self.invoice.aeat_state,
                "cancel_incorrect",
                "Invoice should be marked as incorrect cancellation"
                "after VERI*FACTU processing.",
            )

            # now send the cancellation to verifactu with a cancellation with errors response
            self.invoice.cancel_verifactu()
            json_file = "verifactu_mocked_response_cancel_with_errors.json"
            self.mock_test(mock_connect, json_file)
            self.assertEqual(
                self.invoice.aeat_state,
                "cancel_w_errors",
                "Invoice should be marked as cancelled with errors"
                "after VERI*FACTU processing.",
            )

            # finally send the cancellation to verifactu with a correct cancellation response
            self.invoice.cancel_verifactu()
            json_file = "verifactu_mocked_response_cancel.json"
            self.mock_test(mock_connect, json_file)
            self.assertEqual(
                self.invoice.aeat_state,
                "cancel",
                "Invoice should be marked as cancelled after VERI*FACTU processing.",
            )

    def test_verifactu_macrodata(self):
        """Test verifactu_macrodata computation."""
        self.assertFalse(self.invoice.verifactu_macrodata)
        self.invoice.invoice_line_ids.price_unit = 130000000
        self.assertTrue(self.invoice.verifactu_macrodata)

    def test_verifactu_macrodata_reported(self):
        """Macrodato must be reported as "S" in the RegistroAlta when the total
        is over the limit; otherwise AEAT rejects the record (error 1139).

        The omission case (normal amount -> no Macrodato) is already covered by
        the reference-JSON tests, whose fixtures contain no Macrodato key."""
        self._activate_certificate(self.certificate_password)
        self.invoice.invoice_line_ids.price_unit = 130000000
        self.invoice.action_post()
        self.assertEqual(
            self.invoice._get_verifactu_invoice_dict()["RegistroAlta"].get("Macrodato"),
            "S",
        )


class TestVerifactuSchemaValidation(TestVerifactuCommon):
    """Records that do not match the official schema must not break the batch."""

    def setUp(self):
        super().setUp()
        self._activate_certificate(self.certificate_password)
        self.entry_model = self.env["verifactu.invoice.entry"]

    def _create_pending_invoice(self, **kwargs):
        """Invoice that will enter the sending queue once posted.

        `_create_test_invoice` marks invoices as already sent, so they never
        reach the cron; this resets that.
        """
        invoice = self._create_test_invoice(**kwargs)
        invoice.aeat_state = "not_sent"
        return invoice

    def _post_batch(self):
        """Post three invoices sharing the company chaining."""
        batch = (
            self.invoice
            + self._create_pending_invoice(amount=200)
            + self._create_pending_invoice(amount=300)
        )
        batch.action_post()
        return batch

    def _patch_dict(self, documents, transform):
        """Patch the payload builder, applying `transform` only to `documents`."""
        move_class = type(self.env["account.move"])
        original = move_class._get_verifactu_invoice_dict

        def _fake(record, cancel=False):
            if record.id in documents.ids:
                return transform(record, original)
            return original(record, cancel=cancel)

        return patch.object(move_class, "_get_verifactu_invoice_dict", _fake)

    def _empty_breakdown(self, record, original):
        inv_dict = original(record)
        inv_dict["RegistroAlta"]["Desglose"] = {"DetalleDesglose": []}
        return inv_dict

    def _raise_build_error(self, record, original):
        raise UserError(_("Tax is not mapped to VERI*FACTU."))

    def test_validate_registro_accepts_real_payload(self):
        """The serializer must produce a schema-valid document for a good invoice."""
        self.invoice.action_post()
        inv_dict = self.invoice._get_verifactu_invoice_dict()
        self.assertIsNone(
            self.invoice._validate_verifactu_registro(inv_dict),
            "A correct invoice must validate: a failure here means the serializer "
            "emits elements in an order the schema does not allow.",
        )

    def test_validate_registro_rejects_empty_breakdown(self):
        """The known offending case must be caught, naming its element."""
        self.invoice.action_post()
        inv_dict = self.invoice._get_verifactu_invoice_dict()
        inv_dict["RegistroAlta"]["Desglose"] = {"DetalleDesglose": []}
        error = self.invoice._validate_verifactu_registro(inv_dict)
        self.assertIn("DetalleDesglose", error or "")
        self.assertNotIn(
            "{", error or "", "The namespace URI must be stripped from the message."
        )

    def test_post_blocks_invoice_not_matching_schema(self):
        """V1 — prevention: an invalid record must not be posted at all."""
        with self._patch_dict(self.invoice, self._empty_breakdown):
            with self.assertRaises(UserError) as error:
                self.invoice.action_post()
        self.assertIn(
            "DetalleDesglose",
            str(error.exception),
            "The error must name the schema element at fault so it can be fixed.",
        )

    def test_post_reports_every_invoice_not_matching_schema(self):
        """A mass posting must name every offender, not only the first one."""
        offenders = self.invoice + self._create_pending_invoice(amount=500)
        with self._patch_dict(offenders, self._empty_breakdown):
            with self.assertRaises(UserError) as error:
                offenders.action_post()
        message = str(error.exception)
        self.assertEqual(
            message.count("DetalleDesglose"),
            2,
            "Both offending invoices must be reported by a single posting, so "
            "that a mass posting is not repeated once per offending invoice.",
        )
        for invoice in offenders:
            self.assertIn(
                invoice.name,
                message,
                "Each offender must be named: the error is only actionable if "
                "it says which invoice to fix.",
            )

    def test_post_reports_build_failure_next_to_schema_error(self):
        """A record that cannot be built belongs in the same report.

        It will not reach the Agency either, so raising it on the spot would
        abort the posting at its first offender and force a mass posting to be
        repeated once per bad invoice — what reporting every one of them
        avoids.
        """
        unbuildable = self._create_pending_invoice(amount=500)
        offenders = self.invoice + unbuildable
        with self._patch_dict(self.invoice, self._empty_breakdown), self._patch_dict(
            unbuildable, self._raise_build_error
        ):
            with self.assertRaises(UserError) as error:
                offenders.action_post()
        message = str(error.exception)
        for invoice in offenders:
            self.assertIn(
                invoice.name,
                message,
                "Both offenders must be named, whatever stopped each of them: "
                "a build failure raised on its own would name neither.",
            )
        self.assertEqual(
            message.count("DetalleDesglose"),
            1,
            "Only one of them broke the schema; the other never got built.",
        )

    def test_check_failing_does_not_stop_the_post(self):
        """A failure of the check itself must not stop the invoice being posted.

        Mirror of `test_check_failing_does_not_stop_the_batch` on the posting
        side: turning that fail-open into a raise would stop all invoicing, and
        nothing else in the suite would notice.
        """
        move_class = type(self.env["account.move"])

        def _boom(record, inv_dict):
            raise RuntimeError("the schema could not be read")

        with patch.object(move_class, "_validate_verifactu_registro", _boom):
            self.invoice.action_post()
        self.assertEqual(
            self.invoice.state,
            "posted",
            "What the check protects against is a record the Agency would "
            "reject, not the check being unable to run.",
        )

    def test_long_description_is_truncated(self):
        """A description over the limit must be normalised, not block the post.

        It is set on the company, so blocking would stop every invoice at once
        and the user could not fix it from the invoice.
        """
        self.invoice.verifactu_description = "L" * 600
        self.invoice.action_post()
        inv_dict = self.invoice._get_verifactu_invoice_dict()
        self.assertEqual(
            len(inv_dict["RegistroAlta"]["DescripcionOperacion"]),
            500,
            "The description must be cut to the length the schema allows.",
        )
        self.assertIsNone(
            self.invoice._validate_verifactu_registro(inv_dict),
            "Once truncated, the record must validate.",
        )

    def test_tax_rate_with_extra_decimals_is_rounded(self):
        """A rate the schema cannot express must be rounded, not block the post.

        `account.tax.amount` holds four decimals and the schema takes two, so
        a rate such as 7.527 would otherwise block every invoice using it.
        """
        tax = self.invoice.invoice_line_ids.tax_ids[:1]
        self.assertTrue(tax, "The fixture invoice is expected to carry a tax.")
        tax.amount = 7.527
        self.invoice.action_post()
        inv_dict = self.invoice._get_verifactu_invoice_dict()
        rates = [
            detail["TipoImpositivo"]
            for detail in inv_dict["RegistroAlta"]["Desglose"]["DetalleDesglose"]
        ]
        self.assertIn(
            "7.53",
            rates,
            "The rate must be rounded to the two decimals of the schema.",
        )
        self.assertIsNone(
            self.invoice._validate_verifactu_registro(inv_dict),
            "Once rounded, the record must validate.",
        )

    def test_rounded_rate_stays_within_the_reported_amount_tolerance(self):
        """Rounding the rate must not put the record outside what is admitted.

        The Agency validates `CuotaRepercutida = BaseImponibleOimporteNoSujeto
        * TipoImpositivo / 100 +/- 10,00 euros` (Validaciones y errores 15.7),
        and the amount travels as the invoice computed it, from the real rate.
        Rounding the rate to what the schema can express therefore has to stay
        inside that margin, which is what this fixes: on a base of 10.000 the
        widest possible rounding moves the pair by 0,50 euros.
        """
        tax = self.invoice.invoice_line_ids.tax_ids[:1]
        self.assertTrue(tax, "The fixture invoice is expected to carry a tax.")
        # Before creating it, so that the invoice computes its amount from the
        # rate under test: changing the rate afterwards leaves the amount of
        # the previous one, which is not a case that can reach the Agency.
        tax.amount = 7.527
        invoice = self._create_pending_invoice(amount=10000)
        invoice.action_post()
        inv_dict = invoice._get_verifactu_invoice_dict()
        checked = 0
        for detail in inv_dict["RegistroAlta"]["Desglose"]["DetalleDesglose"]:
            if "CuotaRepercutida" not in detail:
                continue
            base = float(detail["BaseImponibleOimporteNoSujeto"])
            rate = float(detail["TipoImpositivo"])
            reported = float(detail["CuotaRepercutida"])
            checked += 1
            self.assertLess(
                abs(reported - base * rate / 100),
                10.00,
                "The amount reported and the rounded rate must stay within the "
                "margin the Agency admits between them.",
            )
        self.assertTrue(checked, "The breakdown must carry an amount to check.")

    def test_skip_schema_check_only_lifts_the_posting_gate(self):
        """The escape hatch must not let an invalid record reach the Agency.

        It exists to keep invoicing while a wrong rejection is looked into, so
        it lifts the gate at posting and nothing else.
        """
        self.company.verifactu_skip_schema_check = True
        with self._patch_dict(self.invoice, self._empty_breakdown):
            self.invoice.action_post()
            self.assertEqual(
                self.invoice.state,
                "posted",
                "With the check skipped, the invoice must post.",
            )
            entry = self.invoice.last_verifactu_invoice_entry_id
            self.assertTrue(entry, "Posting must still queue the record.")
            _registros, valid, failures = entry._build_verifactu_registro_list()
        self.assertFalse(
            valid,
            "The record must still be left out of the batch: skipping the "
            "posting gate must not send what the Agency would reject.",
        )
        self.assertIn(
            entry.id,
            failures,
            "The excluded record must still be attributed its own error.",
        )

    def test_check_failing_does_not_stop_the_batch(self):
        """A failure of the check itself must not stop the batch being sent.

        Same policy as when posting: what the check protects against is a
        record the Agency would reject, not the check being unable to run.
        """
        batch = self._post_batch()
        move_class = type(self.env["account.move"])

        def _boom(record, inv_dict):
            raise RuntimeError("the schema could not be read")

        with patch.object(move_class, "_validate_verifactu_registro", _boom):
            (
                registros,
                valid,
                failures,
            ) = batch.last_verifactu_invoice_entry_id._build_verifactu_registro_list()
        self.assertFalse(
            failures,
            "A broken check must not be attributed to the records as if they "
            "were the ones at fault.",
        )
        self.assertEqual(
            len(registros),
            len(batch),
            "Every record must still be sent when the check cannot run.",
        )

    def test_schema_is_not_kept_between_calls(self):
        """The validator must not be cached, so it is never shared.

        `lxml` fills the error log of the validator while validating, so two
        threads using the same one can lose the name of the offending element,
        which is the only actionable part of the message.
        """
        self.assertIsNot(
            self.invoice._get_verifactu_schema_tree(),
            self.invoice._get_verifactu_schema_tree(),
            "Caching the schema would share one validator between threads.",
        )

    def _count_schema_exclusions(self, document):
        return self.env["verifactu.invoice.entry.response.line"].search_count(
            [
                ("entry_id", "=", document.last_verifactu_invoice_entry_id.id),
                ("error_code", "=", "SCHEMA_ERROR"),
            ]
        )

    def _exclusion_responses(self, document):
        return (
            self.env["verifactu.invoice.entry.response.line"]
            .search(
                [
                    ("entry_id", "=", document.last_verifactu_invoice_entry_id.id),
                    ("error_code", "=", "SCHEMA_ERROR"),
                ]
            )
            .mapped("entry_response_id")
        )

    def _count_exclusion_activities(self, document):
        """Activities on this document's exclusions only.

        The database carries activities from elsewhere, so counting them all
        would measure the fixtures instead of the behaviour.
        """
        return self.env["mail.activity"].search_count(
            [
                ("res_model", "=", "verifactu.invoice.entry.response"),
                ("res_id", "in", self._exclusion_responses(document).ids),
            ]
        )

    def test_every_pass_leaves_a_trace_but_warns_once(self):
        """Retries must be visible, and the warning must not be repeated.

        The record stays queued on purpose so that it goes out once corrected,
        which means the cron finds it every minute. Each pass leaves its own
        response so the retries can be seen, but the activity is raised once:
        it stays open until somebody attends it, and repeating it every minute
        would bury it.
        """
        batch = self._post_batch()
        culprit = batch[1]
        valid = batch - culprit
        with self._patch_dict(culprit, self._empty_breakdown), patch(
            "odoo.addons.l10n_es_verifactu_oca.models."
            "verifactu_invoice_entry.VerifactuInvoiceEntry._connect_verifactu"
        ) as mock_connect:
            self._mock_batch_service(mock_connect, valid)
            self.entry_model._cron_send_documents_to_verifactu()
            self.entry_model._cron_send_documents_to_verifactu()
            self.entry_model._cron_send_documents_to_verifactu()
        self.assertEqual(
            self._count_schema_exclusions(culprit),
            3,
            "Every pass must leave its trace, or the queue looks abandoned.",
        )
        self.assertEqual(
            self._count_exclusion_activities(culprit),
            1,
            "The warning must be raised once: it stays open until attended.",
        )

    def test_one_warning_per_pass_not_per_send_call(self):
        """A pass splits the batch in two calls but warns once.

        The cron reports the records registered long ago as an incident and
        the rest normally. A record that was never sent belongs to neither, so
        reporting per call would raise two warnings for a single pass.
        """
        batch = self._post_batch()
        # One offender in each of the two groups the cron makes.
        batch[0].last_verifactu_invoice_entry_id.document.write(
            {
                "verifactu_registration_date": fields.Datetime.now()
                - timedelta(seconds=300)
            }
        )
        offenders = batch[0] + batch[1]
        with self._patch_dict(offenders, self._empty_breakdown), patch(
            "odoo.addons.l10n_es_verifactu_oca.models."
            "verifactu_invoice_entry.VerifactuInvoiceEntry._connect_verifactu"
        ) as mock_connect:
            self._mock_batch_service(mock_connect, batch - offenders)
            self.entry_model._cron_send_documents_to_verifactu()
        lines = self.env["verifactu.invoice.entry.response.line"].search(
            [
                (
                    "entry_id",
                    "in",
                    offenders.mapped("last_verifactu_invoice_entry_id").ids,
                ),
                ("error_code", "=", "SCHEMA_ERROR"),
            ]
        )
        self.assertEqual(len(lines), 2, "Each offender must get its own line.")
        self.assertEqual(
            len(lines.mapped("entry_response_id")),
            1,
            "Both lines must hang from a single response: reporting per send "
            "call would raise two warnings for one pass.",
        )

    def test_send_batch_excludes_schema_invalid_entry(self):
        """V1 — one invalid record must not stop the other two."""
        batch = self._post_batch()
        culprit = batch[1]
        valid = batch - culprit
        with self._patch_dict(culprit, self._empty_breakdown), patch(
            "odoo.addons.l10n_es_verifactu_oca.models."
            "verifactu_invoice_entry.VerifactuInvoiceEntry._connect_verifactu"
        ) as mock_connect:
            service = self._mock_batch_service(mock_connect, valid)
            self.entry_model._cron_send_documents_to_verifactu()
        self.assertEqual(
            service.RegFactuSistemaFacturacion.call_count,
            1,
            "The batch must be sent once, without per-record retries.",
        )
        self.assertEqual(
            len(service.RegFactuSistemaFacturacion.call_args[0][1]),
            2,
            "Only the two valid records should have been sent.",
        )
        for invoice in valid:
            self.assertEqual(invoice.aeat_state, "sent")
        self.assertEqual(
            culprit.aeat_state, "not_sent", "The culprit stays queued for a later pass."
        )

    def test_send_batch_error_only_on_culprit(self):
        """V2 — the error belongs to the offending invoice only."""
        batch = self._post_batch()
        culprit = batch[1]
        valid = batch - culprit
        with self._patch_dict(culprit, self._empty_breakdown), patch(
            "odoo.addons.l10n_es_verifactu_oca.models."
            "verifactu_invoice_entry.VerifactuInvoiceEntry._connect_verifactu"
        ) as mock_connect:
            self._mock_batch_service(mock_connect, valid)
            self.entry_model._cron_send_documents_to_verifactu()
        self.assertTrue(culprit.aeat_send_failed)
        self.assertIn(
            "DetalleDesglose",
            culprit.aeat_send_error or "",
            "The stored error must keep the offending element, not a truncation.",
        )
        for invoice in valid:
            self.assertFalse(invoice.aeat_send_failed)
            self.assertFalse(invoice.aeat_send_error)
        lines = self.env["verifactu.invoice.entry.response.line"].search(
            [("error_code", "=", "SCHEMA_ERROR")]
        )
        self.assertEqual(len(lines), 1, "Exactly one response line for the culprit.")
        self.assertEqual(lines.document_id, culprit.id)

    def test_send_batch_build_failure_isolated(self):
        """V1 — a payload that cannot even be built must not abort the pass."""
        batch = self._post_batch()
        culprit = batch[1]
        valid = batch - culprit
        with self._patch_dict(culprit, self._raise_build_error), patch(
            "odoo.addons.l10n_es_verifactu_oca.models."
            "verifactu_invoice_entry.VerifactuInvoiceEntry._connect_verifactu"
        ) as mock_connect:
            self._mock_batch_service(mock_connect, valid)
            self.entry_model._cron_send_documents_to_verifactu()
        for invoice in valid:
            self.assertEqual(invoice.aeat_state, "sent")
        self.assertTrue(culprit.aeat_send_failed)
        self.assertIn("not mapped", culprit.aeat_send_error or "")

    def test_send_batch_schema_failure_raises_activity(self):
        """The exclusion must not be silent: somebody has to be told."""
        responsible_group = self.env.ref(
            "l10n_es_verifactu_oca.group_verifactu_responsible"
        )
        responsible_group.sudo().users = [Command.link(self.env.user.id)]
        batch = self._post_batch()
        culprit = batch[1]
        valid = batch - culprit
        with self._patch_dict(culprit, self._empty_breakdown), patch(
            "odoo.addons.l10n_es_verifactu_oca.models."
            "verifactu_invoice_entry.VerifactuInvoiceEntry._connect_verifactu"
        ) as mock_connect:
            self._mock_batch_service(mock_connect, valid)
            self.entry_model._cron_send_documents_to_verifactu()
        activity = self.env["mail.activity"].search(
            [("res_model", "=", "verifactu.invoice.entry.response")]
        )
        self.assertTrue(
            activity, "An activity must warn the responsible group of the exclusion."
        )
        self.assertIn(
            self.env.user,
            activity.mapped("user_id"),
            "The activity must land on a member of the responsible group.",
        )

    def test_receiver_name_is_truncated(self):
        """A long customer name must be normalised, not block the invoice."""
        self.partner.name = "X" * 130
        self.invoice.action_post()
        inv_dict = self.invoice._get_verifactu_invoice_dict()
        receiver = inv_dict["RegistroAlta"]["Destinatarios"]["IDDestinatario"]
        self.assertEqual(
            len(receiver["NombreRazon"]),
            120,
            "The receiver name must be truncated like the issuer's.",
        )
        self.assertFalse(
            self.invoice._validate_verifactu_registro(inv_dict),
            "The truncated payload must match the schema.",
        )


class TestVerifactuSendResponse(TestVerifactuCommon):
    def test_create_activity_on_exception(self):
        """
        Creates an activity whenever the connection with VERI*FACTU
        is not possible.
        """
        MailActivity = self.env["mail.activity"]
        ActivityType = self.env.ref(
            "l10n_es_verifactu_oca.mail_activity_data_exception"
        )
        # Send an invoice without a certificate
        self.invoice.action_post()
        self.env["verifactu.invoice.entry"]._cron_send_documents_to_verifactu()
        self.assertEqual(self.invoice.aeat_state, "not_sent")
        activity_1 = MailActivity.search(
            [
                ("activity_type_id", "=", ActivityType.id),
                ("res_model", "=", "verifactu.invoice.entry.response"),
            ]
        )
        self.assertTrue(activity_1, "An exception activity should have been created")
        self.invoice.resend_verifactu()
        self.env["verifactu.invoice.entry"]._cron_send_documents_to_verifactu()
        activity_2 = MailActivity.search(
            [
                ("activity_type_id", "=", ActivityType.id),
                ("res_model", "=", "verifactu.invoice.entry.response"),
            ]
        )
        self.assertEqual(
            len(activity_1),
            len(activity_2),
            "There should be only one exception activity created",
        )
        # Activate certificate and re-run the cron
        self._activate_certificate(self.certificate_password)
        self.env["verifactu.invoice.entry"]._cron_send_documents_to_verifactu()
        activity_done = (
            self.env["mail.activity"]
            .with_context(active_test=False)
            .search(
                [
                    ("activity_type_id", "=", ActivityType.id),
                    ("res_model", "=", "verifactu.invoice.entry.response"),
                ]
            )
        )
        # todo: fix this, it's not activity_done.has_recommended_activites,
        #  should check if it's not visible anymore to the user
        self.assertFalse(
            activity_done.has_recommended_activities,
            "The exception activity should not appear.",
        )

    def mock_verifactu_response(self, error_code, description):
        """Recreates a verifactu response"""
        return {
            "CSV": "dummy-csv",
            "RespuestaLinea": [
                {
                    "IDFactura": {
                        "NumSerieFactura": self.invoice.name,
                    },
                    "EstadoRegistro": "AceptadoConErrores",
                    "CodigoErrorRegistro": error_code,
                    "DescripcionErrorRegistro": description,
                }
            ],
        }

    @patch(
        "odoo.addons.l10n_es_verifactu_oca.models.verifactu_invoice_entry."
        "VerifactuInvoiceEntry._connect_verifactu"
    )
    def test_create_send_activity(self, mock_connect):
        """
        Create an activity whenever the response from VERI*FACTU indicates
        that incorrect invoices have been sent
        """
        MailActivity = self.env["mail.activity"]
        ActivityType = self.env.ref("mail.mail_activity_data_warning")
        mock_service = MagicMock()
        module = "l10n_es_verifactu_oca"
        json_file = "verifactu_mocked_response_accepted_with_errors.json"
        path = get_resource_path(module, "tests/json", json_file)
        if not path:
            raise Exception("Incorrect JSON file: %s" % json_file)
        with open(path, "r") as f:
            response_dict = json.loads(f.read())
        self.invoice.action_post()
        # Update the response to match the actual invoice name AFTER posting
        response_dict["RespuestaLinea"][0]["IDFactura"][
            "NumSerieFactura"
        ] = self.invoice.name
        # Set up the mock AFTER updating the JSON
        mock_service.RegFactuSistemaFacturacion.return_value = response_dict
        mock_connect.return_value = mock_service
        self.env["verifactu.invoice.entry"]._cron_send_documents_to_verifactu()
        activity = MailActivity.search(
            [
                ("activity_type_id", "=", ActivityType.id),
                ("res_model", "=", "verifactu.invoice.entry.response"),
                ("summary", "=", "Check incorrect invoices from VERI*FACTU"),
            ]
        )
        self.assertTrue(
            activity,
            "A warning activity should be created for 'AceptadoConErrores' response",
        )

    def test_check_verifactu_configuration_tax_agency(self):
        # The default company uses the Spanish tax agency, which is accepted,
        # so a fully configured invoice passes the configuration check.
        self.invoice._check_verifactu_configuration()
        # A tax agency that is not in the accepted list must be rejected.
        # Regression: this branch used to reference the unbound method
        # ``get_external_id`` and use ``in`` instead of ``not in``, so it never
        # triggered regardless of the configured agency.
        self.company.tax_agency_id = self.env.ref(
            "l10n_es_aeat.aeat_tax_agency_bizkaia"
        )
        with self.assertRaises(UserError):
            self.invoice._check_verifactu_configuration()
