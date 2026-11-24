# Copyright 2026 PYMING - Extreme Micro S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
from unittest.mock import patch
from xml.sax.saxutils import escape

from psycopg2.errors import SerializationFailure

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from ..models import delivery_carrier
from ..models.gls_asm_request import GlsAsmApiError, GlsAsmRequest
from .common import LABEL_PDF, NOT_FOUND, GlsAsmOfflineMixin, soap_response


@tagged("post_install", "-at_install")
class TestDeliveryGlsAsmRecovery(GlsAsmOfflineMixin, TransactionCase):
    """Recover external bookings with real request conversion, never real SOAP."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Synthetic Customer & Co.",
                "street": "Customer Street 2",
                "city": "Madrid",
                "zip": "28002",
                "country_id": cls.env.ref("base.es").id,
            }
        )
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.company.id)], limit=1
        )
        cls.warehouse.partner_id = cls.partner
        cls.warehouse.out_type_id.print_label = True
        cls.product = cls.env["product.product"].create(
            {"name": "Synthetic Recovery Parcel", "type": "consu", "weight": 1}
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Synthetic GLS Recovery",
                "delivery_type": "gls_asm",
                "product_id": cls.env["product.product"]
                .create({"name": "Synthetic Recovery Shipping", "type": "service"})
                .id,
                "gls_asm_shiptime": "3",
                "integration_level": "rate_and_ship",
            }
        )

    def setUp(self):
        super().setUp()
        self.picking = self.env["stock.picking"].create(
            {
                "name": "REC/TEST/1",
                "partner_id": self.partner.id,
                "picking_type_id": self.warehouse.out_type_id.id,
                "location_id": self.warehouse.lot_stock_id.id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "carrier_id": self.carrier.id,
                "number_of_packages": 1,
                "move_ids": [
                    Command.create(
                        {
                            "name": "Synthetic Recovery Parcel",
                            "product_id": self.product.id,
                            "product_uom": self.product.uom_id.id,
                            "product_uom_qty": 1,
                            "location_id": self.warehouse.lot_stock_id.id,
                            "location_dest_id": self.env.ref(
                                "stock.stock_location_customers"
                            ).id,
                        }
                    )
                ],
            }
        )

    def _expedition(self, **overrides):
        values = {
            "refC": self.picking.name.replace("\\", "/"),
            "codexp": "REC-EXP",
            "codbar": "REC-BARCODE",
            "codServicio": self.carrier.gls_asm_service,
            "codHorario": self.carrier.gls_asm_shiptime,
            "bultos": "1",
            "nombre_dst": self.partner.name,
            "calle_dst": self.partner.street,
            "localidad_dst": self.partner.city,
            "cp_dst": self.partner.zip,
            "codpais_dst": "34",
            "tipo_portes": "P",
            "codestado": "-10",
            "estado": "GRABADO",
            # Healthy recorded shipments use S too: it is NOT cancellation.
            "borrado": "S",
            "fecha": "01/01/2000 0:00:00",
        }
        values.update(overrides)
        return (
            "<exp>"
            + "".join(
                f"<{key}>{escape(str(value))}</{key}>" for key, value in values.items()
            )
            + "</exp>"
        )

    def _lookup(self, *expeditions):
        return (
            "<response><expediciones>"
            + "".join(expeditions)
            + "</expediciones></response>"
        )

    def _label_response(self):
        label = base64.b64encode(LABEL_PDF).decode()
        return (
            f"<response><base64Binary>{label}</base64Binary>"
            f"<base64Binary>{label}</base64Binary></response>"
        )

    def _duplicate_response(self, code=-70):
        return (
            f'<response><Servicios><Envio><Resultado return="{code}" />'
            "</Envio></Servicios></response>"
        )

    def _allow_duplicate_recovery(self, **responses):
        """Each recovery starts with one rejected booking, never a preflight."""
        count = len(responses["GetExpCli"])
        self._allow_soap(
            GrabaServicios=[self._duplicate_response()] * count, **responses
        )
        self.duplicate_recovery_count = count

    def tearDown(self):
        try:
            if hasattr(self, "duplicate_recovery_count"):
                self.assertEqual(
                    [
                        call[0]
                        for call in self.soap_service.method_calls
                        if call[0] != "EtiquetaEnvio"
                    ],
                    ["GrabaServicios", "GetExpCli"] * self.duplicate_recovery_count,
                )
        finally:
            super().tearDown()

    def test_recovery_manual_send_preserves_native_links_and_label(self):
        self._allow_duplicate_recovery(
            GetExpCli=[self._lookup(self._expedition())],
            EtiquetaEnvio=[self._label_response()],
        )
        self.picking.send_to_shipper()
        self.assertEqual(self.picking.carrier_tracking_ref, "REC-EXP")
        self.assertEqual(self.picking.gls_asm_public_tracking_ref, "REC-BARCODE")
        self.assertFalse(self.picking.gls_asm_picking_ref)
        self.soap_service.GetExpCli.assert_called_once_with(
            codigo=self.picking.name, uid="SYNTHETIC"
        )
        self.soap_service.EtiquetaEnvio.assert_called_once_with("REC-BARCODE", "PDF")
        self.assertIn("REC-EXP", self.carrier.gls_asm_get_tracking_link(self.picking))
        attachment = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "stock.picking"),
                ("res_id", "=", self.picking.id),
                ("name", "=", "gls_label_REC-BARCODE.pdf"),
            ]
        )
        self.assertEqual(len(attachment), 1)
        self.assertEqual(base64.b64decode(attachment.datas), LABEL_PDF)
        self.assertTrue(
            any(
                "Recovered existing GLS" in (msg.body or "")
                for msg in self.picking.message_ids
            )
        )

    def test_international_recovery_stops_until_mapping_is_verified(self):
        self.partner.country_id = self.env.ref("base.pt")
        self._allow_duplicate_recovery(
            GetExpCli=[self._lookup(self._expedition(codpais_dst="351"))]
        )
        with self.assertRaisesRegex(
            UserError, "international tracking cannot be verified"
        ):
            self.picking.send_to_shipper()
        self.assertFalse(self.picking.carrier_tracking_ref)
        self.soap_service.EtiquetaEnvio.assert_not_called()

    def test_international_booking_keeps_native_creation_references(self):
        self.partner.country_id = self.env.ref("base.pt")
        self._allow_soap(
            GrabaServicios=[
                self._booking_response(
                    "NEW-EXP",
                    "NEW-BAR",
                    "NEW-NATIVE-N",
                    base64.b64encode(LABEL_PDF).decode(),
                )
            ],
        )
        self.picking.send_to_shipper()
        self.assertEqual(self.picking.carrier_tracking_ref, "NEW-EXP")
        self.assertEqual(self.picking.gls_asm_picking_ref, "NEW-NATIVE-N")
        self.assertIn(
            "NEW-NATIVE-N", self.carrier.gls_asm_get_tracking_link(self.picking)
        )
        self.assertEqual(
            [call[0] for call in self.soap_service.method_calls], ["GrabaServicios"]
        )

    def test_conflicting_local_references_stop_without_overwrite(self):
        cases = (
            ("carrier_tracking_ref", "OTHER-EXP"),
            ("carrier_tracking_ref", "REC-EXP,OTHER-EXP"),
            ("gls_asm_public_tracking_ref", "OTHER-BARCODE"),
            ("gls_asm_picking_ref", "UNVERIFIABLE-N"),
        )
        self._allow_duplicate_recovery(
            GetExpCli=[self._lookup(self._expedition())] * len(cases)
        )
        for field, existing in cases:
            self.picking[field] = existing
            with self.subTest(field=field, existing=existing), self.assertRaises(
                UserError
            ):
                self.picking.send_to_shipper()
            self.assertEqual(self.picking[field], existing)
            self.picking[field] = False
        self.soap_service.EtiquetaEnvio.assert_not_called()

    def test_matching_local_references_recover_without_appending(self):
        self.picking.write(
            {
                "carrier_tracking_ref": "REC-EXP",
                "gls_asm_public_tracking_ref": "REC-BARCODE",
            }
        )
        self._allow_duplicate_recovery(
            GetExpCli=[self._lookup(self._expedition())],
            EtiquetaEnvio=[self._label_response()],
        )
        self.picking.send_to_shipper()
        self.assertEqual(self.picking.carrier_tracking_ref, "REC-EXP")
        self.assertEqual(self.picking.gls_asm_public_tracking_ref, "REC-BARCODE")
        self.assertFalse(self.picking.gls_asm_picking_ref)

    def test_cancelled_recovery_requires_gls_review_and_new_picking(self):
        self._allow_duplicate_recovery(
            GetExpCli=[
                self._lookup(self._expedition(codestado=code)) for code in ("5", "51")
            ]
        )
        for code in ("5", "51"):
            with self.subTest(code=code), self.assertRaisesRegex(
                UserError, "new picking"
            ) as error:
                self.picking.send_to_shipper()
            self.assertIn("Review", str(error.exception))
            self.assertNotIn("rename", str(error.exception).lower())
        self.soap_service.EtiquetaEnvio.assert_not_called()

    def test_recovery_during_native_validation(self):
        self._allow_duplicate_recovery(
            GetExpCli=[self._lookup(self._expedition())],
            EtiquetaEnvio=[self._label_response()],
        )
        self.picking.action_confirm()
        self.picking.move_ids.quantity = 1
        self.picking.move_ids.picked = True
        self.picking.button_validate()
        self.assertEqual(self.picking.state, "done")
        self.assertEqual(self.picking.carrier_tracking_ref, "REC-EXP")

    def test_lookup_unescaped_reference_and_strict_result_contract(self):
        self.picking.name = "R\\A&B<1"
        self._allow_duplicate_recovery(
            GetExpCli=[self._lookup(self._expedition())],
            EtiquetaEnvio=[self._label_response()],
        )
        result = self.carrier.gls_asm_send_shipping(self.picking)
        self.assertEqual(result[0]["tracking_number"], "REC-EXP")
        self.assertEqual(result[0]["exact_price"], 0)
        self.soap_service.GetExpCli.assert_called_once_with(
            codigo="R/A&B<1", uid="SYNTHETIC"
        )

    def test_duplicate_numeric_codes_recover_without_another_creation(self):
        lookups = []
        bookings = []
        for code in (-70, -118):
            lookups.append(self._lookup(self._expedition()))
            bookings.append(
                f'<response><Servicios><Envio><Resultado return="{code}" />'
                "</Envio></Servicios></response>"
            )
        self._allow_soap(
            GetExpCli=lookups,
            GrabaServicios=bookings,
            EtiquetaEnvio=[self._label_response()] * 2,
        )
        for code in (-70, -118):
            with self.subTest(code=code):
                result = self.carrier.gls_asm_send_shipping(self.picking)
                self.assertEqual(result[0]["tracking_number"], "REC-EXP")
                self.assertEqual(
                    self.picking.gls_asm_public_tracking_ref, "REC-BARCODE"
                )
                # Simulate the rolled-back transaction before the next attempt.
                self.picking.write(
                    {"gls_asm_public_tracking_ref": False, "gls_asm_picking_ref": False}
                )
        self.assertEqual(
            [call[0] for call in self.soap_service.method_calls],
            ["GrabaServicios", "GetExpCli", "EtiquetaEnvio"] * 2,
        )

    def test_other_creation_error_preserves_structured_user_error(self):
        self._allow_soap(
            GrabaServicios=[
                '<response><Servicios><Envio><Resultado return="-108" />'
                "</Envio></Servicios></response>"
            ],
        )
        with self.assertRaisesRegex(GlsAsmApiError, "Sender Name") as error:
            self.carrier.gls_asm_send_shipping(self.picking)
        self.assertEqual(error.exception.code, -108)
        self.assertIsInstance(error.exception, UserError)
        self.assertEqual(
            [call[0] for call in self.soap_service.method_calls], ["GrabaServicios"]
        )

    def test_booking_transport_failures_do_not_recover(self):
        failures = [
            TimeoutError("Synthetic booking timeout -70"),
            ConnectionError("Synthetic booking connection failure -118"),
        ]
        self._allow_soap(GrabaServicios=[self._duplicate_response()] * len(failures))
        self.soap_service.GrabaServicios.side_effect = failures
        for failure in failures:
            with self.subTest(failure=failure), self.assertRaisesRegex(
                UserError, "No response from server recording"
            ) as raised:
                self.carrier.gls_asm_send_shipping(self.picking)
            self.assertIs(raised.exception.__cause__, failure)
            self.assertNotIsInstance(raised.exception, GlsAsmApiError)
        self.assertEqual(
            [call[0] for call in self.soap_service.method_calls],
            ["GrabaServicios"] * len(failures),
        )

    def test_unstructured_duplicate_message_does_not_recover(self):
        error = UserError("The order number already exists -70 -118")
        with patch.object(delivery_carrier, "GlsAsmRequest") as request:
            request.return_value._send_shipping.side_effect = error
            with self.assertRaises(UserError) as raised:
                self.carrier.gls_asm_send_shipping(self.picking)
            self.assertIs(raised.exception, error)
            request.return_value._send_shipping.assert_called_once()
            request.return_value._find_shipments.assert_not_called()

    def test_duplicate_followup_not_found_preserves_original_error(self):
        self._allow_soap(
            GetExpCli=[NOT_FOUND],
            GrabaServicios=[
                '<response><Servicios><Envio><Resultado return="-118" />'
                "</Envio></Servicios></response>"
            ],
        )
        with self.assertRaises(GlsAsmApiError) as error:
            self.carrier.gls_asm_send_shipping(self.picking)
        self.assertEqual(error.exception.code, -118)
        self.assertEqual(
            [call[0] for call in self.soap_service.method_calls],
            ["GrabaServicios", "GetExpCli"],
        )

    def test_duplicate_not_found_reraises_same_exception(self):
        error = GlsAsmApiError("Synthetic duplicate", code=-70)
        self._allow_soap(GetExpCli=[NOT_FOUND])
        with patch.object(GlsAsmRequest, "_send_shipping", side_effect=error) as book:
            with self.assertRaises(GlsAsmApiError) as raised:
                self.carrier.gls_asm_send_shipping(self.picking)
        self.assertIs(raised.exception, error)
        book.assert_called_once()

    def test_inconclusive_lookup_never_rebooks(self):
        bad_responses = [
            "<response />",
            "<response><expediciones /></response>",
            "<response><expediciones><Error>Account unauthorized</Error>"
            "</expediciones></response>",
            "<response><expediciones><Error>No se encuentra la expedición hoy"
            "</Error></expediciones></response>",
            "<response><expediciones><exp /></expediciones></response>",
            "<response><expediciones><Error>No se encuentra la expedición</Error>"
            "<exp /></expediciones></response>",
        ]
        self._allow_duplicate_recovery(GetExpCli=bad_responses)
        for response in bad_responses:
            with self.subTest(response=response), self.assertRaises(UserError):
                self.carrier.gls_asm_send_shipping(self.picking)

    def test_malformed_lookup_error_does_not_expose_response_values(self):
        self._allow_duplicate_recovery(
            GetExpCli=[
                "<response><expediciones><Error>SYNTHETIC-SECRET-NAME</Error>"
                "<secret_address>SYNTHETIC-SECRET-ADDRESS</secret_address>"
                "</expediciones></response>"
            ]
        )
        with self.assertRaises(UserError) as error:
            self.carrier.gls_asm_send_shipping(self.picking)
        message = str(error.exception)
        self.assertIn("Response structure: root=dict, expediciones=dict", message)
        self.assertNotIn("SYNTHETIC-SECRET", message)
        self.assertNotIn("secret_address", message)

    def test_invalid_base64_label_is_recoverable_user_error(self):
        self._allow_duplicate_recovery(
            GetExpCli=[self._lookup(self._expedition())],
            EtiquetaEnvio=["<response><base64Binary>A</base64Binary></response>"],
        )
        with self.assertRaisesRegex(UserError, "missing or invalid PDF"):
            self.picking.send_to_shipper()
        self.assertFalse(self.picking.carrier_tracking_ref)

    def test_duplicate_lookup_transport_failure_never_rebooks(self):
        self._allow_duplicate_recovery(GetExpCli=[NOT_FOUND])
        self.soap_service.GetExpCli.side_effect = TimeoutError("Synthetic timeout")
        with self.assertRaisesRegex(UserError, "Synthetic timeout"):
            self.carrier.gls_asm_send_shipping(self.picking)

    def test_multiple_candidates_never_rebook_even_if_one_matches(self):
        self._allow_duplicate_recovery(
            GetExpCli=[self._lookup(self._expedition(), self._expedition(refC="OTHER"))]
        )
        with self.assertRaisesRegex(UserError, "2 shipments"):
            self.carrier.gls_asm_send_shipping(self.picking)

    def test_incompatible_candidates_never_rebook(self):
        cases = [
            {"refC": "OTHER"},
            {"refC": "REC/TEST"},
            {"codexp": ""},
            {"codbar": ""},
            {"codestado": ""},
            {"codServicio": "96"},
            {"codHorario": "0"},
            {"tipo_portes": "D"},
            {"bultos": "2"},
            {"bultos": "1.5"},
            {"bultos": ""},
            {"cp_dst": "28001"},
            {"codpais_dst": "351"},
            {"nombre_dst": "Synthetic"},
            {"calle_dst": "Customer Street 22"},
            {"localidad_dst": "Other City"},
        ]
        self._allow_duplicate_recovery(
            GetExpCli=[self._lookup(self._expedition(**case)) for case in cases]
        )
        for case in cases:
            with self.subTest(case=case), self.assertRaisesRegex(
                UserError, "does not match"
            ):
                self.carrier.gls_asm_send_shipping(self.picking)
        self.assertFalse(self.picking.gls_asm_public_tracking_ref)

    def test_malformed_candidate_values_fail_without_links_or_label(self):
        self._allow_duplicate_recovery(
            GetExpCli=[
                self._lookup(self._expedition(codexp="", codbar="")),
                self._lookup(self._expedition()),
            ]
        )
        original = GlsAsmRequest._get_delivery_info
        responses = iter((None, {"value": "REC-EXP"}))

        def malformed(request, reference=False):
            result = original(request, reference)
            result["expediciones"]["exp"]["codexp"] = next(responses)
            return result

        with patch.object(GlsAsmRequest, "_get_delivery_info", malformed):
            for _case in range(2):
                with self.assertRaisesRegex(UserError, "malformed shipment details"):
                    self.picking.send_to_shipper()
        self.assertFalse(self.picking.carrier_tracking_ref)
        self.assertFalse(self.picking.gls_asm_public_tracking_ref)
        self.soap_service.EtiquetaEnvio.assert_not_called()

    def test_optional_parcelshop_payload_code_fails_closed(self):
        self._allow_duplicate_recovery(GetExpCli=[self._lookup(self._expedition())])
        carrier_class = self.env.registry["delivery.carrier"]
        original = carrier_class._prepare_gls_asm_shipping

        def with_code(carrier, picking):
            vals = original(carrier, picking)
            vals["destinatario_codigo"] = "SYNTHETIC-CODE"
            return vals

        with patch.object(carrier_class, "_prepare_gls_asm_shipping", with_code):
            with self.assertRaisesRegex(
                UserError, "ParcelShop code cannot be verified"
            ):
                self.picking.send_to_shipper()
        self.assertFalse(self.picking.gls_asm_public_tracking_ref)

    def test_cod_return_and_parcelshop_fail_closed_when_unverifiable(self):
        cases = [
            {"gls_asm_cash_on_delivery": True},
            {"gls_asm_cash_on_delivery": False, "gls_asm_with_return": True},
            {"gls_asm_with_return": False, "gls_asm_shiptime": "19"},
            {"gls_asm_shiptime": "3", "gls_asm_service": "58"},
        ]
        self._allow_duplicate_recovery(
            GetExpCli=[
                self._lookup(self._expedition()),
                self._lookup(self._expedition()),
                self._lookup(self._expedition(codHorario="19")),
                self._lookup(self._expedition(codServicio="58")),
            ]
        )
        for case in cases:
            self.carrier.write(case)
            with self.subTest(case=case), self.assertRaisesRegex(
                UserError, "cannot be verified"
            ):
                self.carrier.gls_asm_send_shipping(self.picking)

    def test_missing_label_stops_validation_then_retry_and_reprint(self):
        self._allow_duplicate_recovery(
            GetExpCli=[self._lookup(self._expedition())] * 2,
            EtiquetaEnvio=[
                "<response />",
                self._label_response(),
                self._label_response(),
            ],
        )
        self.picking.action_confirm()
        self.picking.move_ids.quantity = 1
        self.picking.move_ids.picked = True
        with self.assertRaisesRegex(UserError, "missing or invalid PDF"):
            # Simulate the RPC transaction rollback after the propagated error.
            with self.env.cr.savepoint():
                self.picking.button_validate()
        self.assertNotEqual(self.picking.state, "done")
        self.assertFalse(self.picking.carrier_tracking_ref)
        self.assertFalse(self.picking.gls_asm_public_tracking_ref)
        self.assertFalse(self.picking.gls_asm_picking_ref)
        self.assertFalse(self.picking.message_ids.attachment_ids)
        self.picking.button_validate()
        self.assertEqual(self.picking.state, "done")
        self.assertEqual(self.picking.carrier_tracking_ref, "REC-EXP")
        self.assertTrue(
            self.picking.message_ids.attachment_ids.filtered(
                lambda att: att.name == "gls_label_REC-BARCODE.pdf"
            )
        )
        self.picking.gls_asm_get_label()
        self.assertTrue(
            self.picking.message_ids.attachment_ids.filtered(
                lambda att: att.name == "gls_REC-BARCODE.pdf"
            )
        )

    def test_label_failure_retry_after_rollback_still_reuses(self):
        self._allow_duplicate_recovery(
            GetExpCli=[self._lookup(self._expedition())] * 2,
            EtiquetaEnvio=[self._label_response()] * 2,
        )
        self.soap_service.EtiquetaEnvio.side_effect = [
            TimeoutError("Synthetic label timeout"),
            soap_response(self._label_response()),
        ]
        with self.assertRaisesRegex(UserError, "Synthetic label timeout"):
            with self.env.cr.savepoint():
                self.picking.send_to_shipper()
        self.assertFalse(self.picking.carrier_tracking_ref)
        self.picking.send_to_shipper()
        self.assertEqual(self.picking.carrier_tracking_ref, "REC-EXP")

    def test_native_db_error_after_recovery_rollback_then_retry(self):
        self._allow_duplicate_recovery(
            GetExpCli=[self._lookup(self._expedition())] * 2,
            EtiquetaEnvio=[self._label_response()] * 2,
        )
        with self.assertRaises(SerializationFailure), self.env.cr.savepoint():
            self.picking.send_to_shipper()
            raise SerializationFailure("Synthetic post-booking failure")
        self.assertFalse(self.picking.carrier_tracking_ref)
        self.picking.send_to_shipper()
        self.assertEqual(self.picking.carrier_tracking_ref, "REC-EXP")

    def test_pending_flush_failure_prevents_external_creation(self):
        with patch.object(delivery_carrier, "GlsAsmRequest") as request:
            with self.assertRaises(SerializationFailure):
                with patch.object(
                    type(self.env),
                    "flush_all",
                    side_effect=SerializationFailure("Synthetic flush"),
                ):
                    self.carrier.gls_asm_send_shipping(self.picking)
            request.return_value._send_shipping.assert_not_called()
            request.return_value._find_shipments.assert_not_called()

    def test_pickup_shipping_does_not_lookup(self):
        self.carrier.gls_asm_service = "7"
        # The historical shipping method skips pickup services entirely.
        with patch.object(delivery_carrier, "GlsAsmRequest") as request:
            result = self.carrier.gls_asm_send_shipping(self.picking)
            self.assertEqual(result, [])
            request.return_value._find_shipments.assert_not_called()
            request.return_value._send_shipping.assert_not_called()

    def test_existing_local_links_not_found_never_rebook(self):
        self._allow_duplicate_recovery(GetExpCli=[NOT_FOUND] * 3)
        for field in (
            "carrier_tracking_ref",
            "gls_asm_public_tracking_ref",
            "gls_asm_picking_ref",
        ):
            self.picking[field] = "SYNTHETIC-EXISTING"
            with self.subTest(field=field), self.assertRaises(GlsAsmApiError) as raised:
                self.carrier.gls_asm_send_shipping(self.picking)
            self.assertEqual(raised.exception.code, -70)
            self.assertEqual(self.picking[field], "SYNTHETIC-EXISTING")
            self.picking[field] = False

    def test_single_label_element_decodes_as_pdf(self):
        label = base64.b64encode(LABEL_PDF).decode()
        self._allow_duplicate_recovery(
            GetExpCli=[self._lookup(self._expedition())],
            EtiquetaEnvio=[
                f"<response><base64Binary>{label}</base64Binary></response>"
            ],
        )
        self.picking.send_to_shipper()
        attachment = self.picking.message_ids.attachment_ids.filtered(
            lambda att: att.name == "gls_label_REC-BARCODE.pdf"
        )
        self.assertEqual(base64.b64decode(attachment.datas), LABEL_PDF)

    def test_invalid_pdf_never_rebooks(self):
        label = base64.b64encode(b"Synthetic error not a PDF").decode()
        self._allow_duplicate_recovery(
            GetExpCli=[self._lookup(self._expedition())],
            EtiquetaEnvio=[
                f"<response><base64Binary>{label}</base64Binary></response>"
            ],
        )
        with self.assertRaisesRegex(UserError, "invalid PDF"):
            self.picking.send_to_shipper()
        self.assertFalse(self.picking.carrier_tracking_ref)

    def test_list_candidate_and_text_normalization(self):
        self._allow_duplicate_recovery(
            GetExpCli=[
                self._lookup(
                    self._expedition(
                        nombre_dst=" SYNTHETIC CUSTOMER & CO. ",
                        calle_dst="Cústomer  Street 2",
                        localidad_dst="MADRID",
                    )
                )
            ],
            EtiquetaEnvio=[self._label_response()],
        )
        original = GlsAsmRequest._get_delivery_info

        def as_list(request, reference=False):
            # Exercise the list convention used for several expeditions.
            result = original(request, reference)
            result["expediciones"]["exp"] = [result["expediciones"]["exp"]]
            return result

        with patch.object(GlsAsmRequest, "_get_delivery_info", as_list):
            self.picking.send_to_shipper()
        self.assertEqual(self.picking.carrier_tracking_ref, "REC-EXP")

    def test_recovery_ignores_gls_street_punctuation_and_symbols(self):
        # GLS returns U+00B4 instead of the apostrophe and drops U+00B0.
        self.partner.street = "Carrer d\u0027Europa 12, 5\u00b0A"
        self._allow_duplicate_recovery(
            GetExpCli=[
                self._lookup(self._expedition(calle_dst="Carrer d\u00b4Europa 12, 5A"))
            ],
            EtiquetaEnvio=[self._label_response()],
        )
        self.picking.send_to_shipper()
        self.assertEqual(self.picking.carrier_tracking_ref, "REC-EXP")

    def test_text_normalization_keeps_letters_digits_and_boundaries(self):
        normalize = self.carrier._gls_asm_normalize_text
        for ours, theirs in (
            ("Carrer d'Europa 12, 5°A", "Carrer d´Europa 12, 5A"),
            ("Carrer d\u2019Europa 12, 5ºA", "carrer d`europa 12, 5a"),
            ("Plaça Major 3, 2ª", "PLACA MAJOR 3, 2"),
            ("Synthetic Customer & Co.", " SYNTHETIC CUSTOMER & CO. "),
            ("Calle 12-14", "Calle 12 14"),
        ):
            with self.subTest(ours=ours, theirs=theirs):
                self.assertEqual(normalize(ours), normalize(theirs))
        for ours, theirs in (
            ("Customer Street 2", "Customer Street 22"),
            ("Calle 12-14", "Calle 1214"),
            ("Carrer d'Europa 12, 5°A", "Carrer d´Europa 12, 5B"),
            ("Madrid", "Other City"),
            ("Ñandú 1", "Nandu 1A"),
        ):
            with self.subTest(ours=ours, theirs=theirs):
                self.assertNotEqual(normalize(ours), normalize(theirs))

    def test_new_booking_rollback_then_duplicate_recovers_older_expedition(self):
        # The external write survives rollback. If GLS rejects the retry as a
        # duplicate, recovery accepts a compatible older expedition. This does
        # not establish that GLS enforces reference uniqueness across dates.
        self._allow_soap(
            GetExpCli=[self._lookup(self._expedition())],
            GrabaServicios=[
                self._booking_response(
                    "REC-EXP", "REC-BARCODE", "", base64.b64encode(LABEL_PDF).decode()
                ),
                self._duplicate_response(),
            ],
            EtiquetaEnvio=[self._label_response()],
        )
        with self.assertRaises(SerializationFailure), self.env.cr.savepoint():
            self.picking.send_to_shipper()
            raise SerializationFailure("Synthetic DB failure after external write")
        self.assertFalse(self.picking.carrier_tracking_ref)
        self.picking.send_to_shipper()
        self.assertEqual(self.picking.carrier_tracking_ref, "REC-EXP")
        self.assertEqual(
            [call[0] for call in self.soap_service.method_calls],
            ["GrabaServicios", "GrabaServicios", "GetExpCli", "EtiquetaEnvio"],
        )
