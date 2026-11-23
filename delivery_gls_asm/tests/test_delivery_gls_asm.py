# Copyright 2026 Studio73 - Pablo Cortés <pablo.cortes@studio73.es>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
# Copyright 2020 Tecnativa - David Vidal
# Copyright 2021 Tecnativa - Víctor Martínez

from unittest import mock

import requests

from odoo.exceptions import UserError
from odoo.tests import Form
from odoo.tools import mute_logger

from odoo.addons.base.tests.common import BaseCommon

from .gls_soap import REQUEST_PATH, FakeGlsClient, FakeGlsService, SoapNode, asdict


class TestDeliveryGlsAsm(BaseCommon):
    _test_user_groups = (
        "base.group_user",
        "stock.group_stock_manager",
        "sales_team.group_sale_manager",
    )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.shipping_product = cls.env["product.product"].create(
            {"type": "service", "name": "Test Shipping costs", "list_price": 10.0}
        )
        cls.carrier_gls_asm = cls.env["delivery.carrier"].create(
            {
                "name": "GLS ASM",
                "delivery_type": "gls_asm",
                "product_id": cls.shipping_product.id,
                "prod_environment": False,
                "gls_asm_service": "37",
            }
        )
        cls.product = cls.env["product.product"].create(
            {"is_storable": True, "name": "Test product"}
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Mr. Odoo & Co.",
                "city": "Odoo Ville",
                "zip": "28001",
                "street": "Calle de La Rua, 3",
            }
        )
        cls.sender_partner = cls.env.company.partner_id
        cls.sender_partner.write(
            {
                "street": "Calle del Almacen, 1",
                "city": "Odoo Ville",
                "zip": "28002",
            }
        )
        order_form = Form(cls.env["sale.order"].with_context(tracking_disable=True))
        order_form.partner_id = cls.partner
        with order_form.order_line.new() as line:
            line.product_id = cls.product
            line.product_uom_qty = 20.0
        cls.sale_order = order_form.save()
        cls.sale_order.carrier_id = cls.carrier_gls_asm.id
        cls.sale_order.action_confirm()
        cls.picking = cls.sale_order.picking_ids
        cls.picking.picking_type_id.warehouse_id.partner_id = cls.sender_partner
        cls.picking.move_ids.quantity = 20
        cls.picking.number_of_packages = 2

    def _patch_gls(self) -> FakeGlsService:
        FakeGlsClient.service = FakeGlsService()
        client_patch = mock.patch(f"{REQUEST_PATH}.Client", FakeGlsClient)
        asdict_patch = mock.patch(f"{REQUEST_PATH}.asdict", asdict)
        client_patch.start()
        asdict_patch.start()
        self.addCleanup(client_patch.stop)
        self.addCleanup(asdict_patch.stop)
        return FakeGlsClient.service

    def test_01_gls_escaping(self):
        vals = self.carrier_gls_asm._prepare_gls_asm_shipping(self.picking)
        self.assertEqual(vals.get("destinatario_nombre"), "Mr. Odoo &amp; Co.")

    def test_02_gls_shipping_packages_reference_and_label(self):
        service = self._patch_gls()
        self.picking.name = "ODOO-REF-TOO-LONG"
        with self.assertRaises(UserError):
            self.picking.button_validate()
        self.picking.name = "ODOO-0001"
        self.picking.button_validate()
        self.assertEqual(self.picking.carrier_tracking_ref, "EXP0000000000001")
        self.assertEqual(self.picking.gls_asm_public_tracking_ref, "BAR0000000000001")
        self.assertEqual(self.picking.gls_asm_picking_ref, "INT0000000000001")
        self.assertEqual(self.picking.number_of_packages, 2)
        attachment = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "stock.picking"),
                ("res_id", "=", self.picking.id),
                ("name", "=", "gls_label_BAR0000000000001.pdf"),
            ]
        )
        self.assertTrue(attachment)
        shipping_xml = next(
            call[1] for call in service.calls if call[0] == "GrabaServicios"
        )
        self.assertIn("<Bultos>2</Bultos>", shipping_xml)
        self.assertIn("ODOO-0001", shipping_xml)

    def test_03_gls_pickup_and_tracking(self):
        self._patch_gls()
        self.carrier_gls_asm.gls_asm_service = "56"
        self.assertTrue(self.carrier_gls_asm.gls_is_pickup_service)
        self.picking.gls_asm_send_pickup()
        self.assertEqual(self.picking.carrier_tracking_ref, "REC0000000000001")
        self.assertEqual(self.picking.gls_asm_public_tracking_ref, "REC0000000000001")
        self.assertEqual(self.picking.gls_pickup_state, "recorded")
        self.assertEqual(self.picking.delivery_state, "shipping_recorded_in_carrier")
        self.assertIn("SOLICITADA", self.picking.tracking_state_history)

    def test_04_gls_cancel_shipment_and_pickup(self):
        self._patch_gls()
        self.picking.name = "ODOO-0001"
        self.picking.button_validate()
        self.picking.cancel_shipment()
        self.assertFalse(self.picking.carrier_tracking_ref)
        self.assertFalse(self.picking.gls_asm_public_tracking_ref)
        self.assertFalse(self.picking.gls_asm_picking_ref)
        self.assertEqual(self.picking.delivery_state, "canceled_shipment")
        self.carrier_gls_asm.gls_asm_service = "56"
        self.picking.gls_asm_send_pickup()
        self.picking.cancel_shipment()
        self.assertFalse(self.picking.carrier_tracking_ref)
        self.assertFalse(self.picking.gls_asm_public_tracking_ref)
        self.assertEqual(self.picking.delivery_state, "canceled_shipment")

    def test_05_gls_cancel_rejection(self):
        service = self._patch_gls()
        self.picking.name = "ODOO-0001"
        self.picking.button_validate()
        service.cancel_return = "-204"
        service.cancel_value = "Tiene tracking operativo"
        with self.assertRaises(UserError):
            self.picking.cancel_shipment()
        self.assertEqual(self.picking.carrier_tracking_ref, "EXP0000000000001")
        self.assertEqual(self.picking.gls_asm_public_tracking_ref, "BAR0000000000001")
        self.assertNotEqual(self.picking.delivery_state, "canceled_shipment")
        bodies = [message.body or "" for message in self.picking.message_ids]
        self.assertFalse(any("cancelled" in body for body in bodies))
        service.cancel_error = True
        with (
            mute_logger("odoo.addons.delivery_gls_asm.models.gls_asm_request"),
            self.assertRaises(UserError),
        ):
            self.picking.cancel_shipment()
        self.assertEqual(self.picking.carrier_tracking_ref, "EXP0000000000001")

    def test_06_gls_manifest(self):
        self._patch_gls()
        self.picking.name = "ODOO-0001"
        self.picking.button_validate()
        wizard = self.env["gls.asm.minifest.wizard"].create(
            {
                "carrier_id": self.carrier_gls_asm.id,
                "date_from": self.picking.date_done.date(),
            }
        )
        captured = {}

        def _report_action(report, docids, data=None, config=None):
            captured["data"] = data
            return {"type": "ir.actions.report", "report_name": report.report_name}

        with mock.patch(
            "odoo.addons.base.models.ir_actions_report.IrActionsReport.report_action",
            _report_action,
        ):
            action = wizard.get_manifest()
        self.assertEqual(action["type"], "ir.actions.report")
        delivery = captured["data"]["deliveries"][0]
        self.assertEqual(delivery["codexp"], "EXP0000000000001")
        self.assertEqual(delivery["nombre_dst"], "Mr. Odoo & Co.")
        self.assertEqual(delivery["bultos"], 2)
        self.assertIn("kgs", delivery)
        empty_wizard = wizard.copy({"date_from": "2050-05-31"})
        with self.assertRaises(UserError):
            empty_wizard.get_manifest()

    def test_07_gls_shipping_values_and_rejections(self):
        self.carrier_gls_asm.gls_asm_with_return = True
        self.carrier_gls_asm.gls_asm_cash_on_delivery = True
        self.partner.street2 = "2"
        self.partner.phone = "600123123"
        self.sender_partner.street2 = "Bajo"
        vals = self.carrier_gls_asm._prepare_gls_asm_shipping(self.picking)
        self.assertEqual(vals["retorno"], "1")
        self.assertEqual(
            float(vals["importes_reembolso"]), self.sale_order.amount_total
        )
        self.assertIn("2", vals["destinatario_direccion"])
        self.partner.street = False
        self.partner.street2 = False
        with self.assertRaises(UserError):
            self.carrier_gls_asm._prepare_gls_asm_shipping(self.picking)
        self.partner.street = "Calle de La Rua, 3"
        self.sender_partner.street = False
        self.sender_partner.street2 = False
        with self.assertRaises(UserError):
            self.carrier_gls_asm._prepare_gls_asm_shipping(self.picking)
        self.sender_partner.street = "Calle del Almacen, 1"
        self.carrier_gls_asm.gls_asm_service = "56"
        with self.assertRaises(UserError):
            self.carrier_gls_asm.gls_asm_send_shipping(self.picking)
        self.partner.street = False
        self.partner.street2 = False
        with self.assertRaises(UserError):
            self.carrier_gls_asm._prepare_gls_asm_pickup(self.picking)
        self.partner.street = "Calle de La Rua, 3"
        self.carrier_gls_asm.gls_asm_service = "37"
        with self.assertRaises(UserError):
            self.carrier_gls_asm.gls_asm_send_pickup(self.picking)
        self.assertFalse(self.picking.gls_asm_send_pickup())
        self.assertFalse(self.picking.gls_asm_get_label())

    def test_08_gls_links_label_and_manifest_wizard(self):
        self.picking.carrier_tracking_ref = "123456"
        link = self.carrier_gls_asm.gls_asm_get_tracking_link(self.picking)
        self.assertIn("123456", link)
        self.assertIn(self.partner.zip, link)
        self.picking.gls_asm_picking_ref = "INT0000000000001"
        self.assertIn(
            "INT0000000000001",
            self.carrier_gls_asm.gls_asm_get_tracking_link(self.picking),
        )
        self.partner.country_id = self.env.ref("base.pt")
        self.assertIn(
            "INT0000000000001",
            self.carrier_gls_asm.gls_asm_get_tracking_link(self.picking),
        )
        self.carrier_gls_asm.prod_environment = True
        self.carrier_gls_asm.gls_asm_uid = "UID-PROD"
        self.assertEqual(self.carrier_gls_asm._gls_asm_uid(), "UID-PROD")
        rate = self.carrier_gls_asm.gls_asm_rate_shipment(self.sale_order)
        self.assertTrue(rate["success"])
        self.assertEqual(rate["price"], self.shipping_product.lst_price)
        action = self.carrier_gls_asm.action_get_manifest()
        self.assertEqual(action["res_model"], "gls.asm.minifest.wizard")
        service = self._patch_gls()
        self.picking.gls_asm_public_tracking_ref = "BAR0000000000001"
        self.picking.gls_asm_get_label()
        self.assertTrue(
            self.env["ir.attachment"].search(
                [
                    ("res_model", "=", "stock.picking"),
                    ("res_id", "=", self.picking.id),
                    ("name", "=", "gls_BAR0000000000001.pdf"),
                ]
            )
        )
        service.label_empty = True
        self.assertFalse(self.carrier_gls_asm.gls_asm_get_label("BAR0000000000001"))
        self.assertFalse(self.carrier_gls_asm.gls_asm_get_label(False))
        service.label_error = True
        with self.assertRaises(UserError):
            self.carrier_gls_asm.gls_asm_get_label("BAR0000000000001")

    def test_09_gls_tracking_states_and_pod(self):
        service = self._patch_gls()
        self.picking.carrier_tracking_ref = "123456"
        service.tracking_exp = {}
        self.carrier_gls_asm.gls_asm_tracking_state_update(self.picking)
        self.assertFalse(self.picking.tracking_state_history)
        service.tracking_exp = {
            "codestado": "20",
            "estado": "INCIDENCIA",
            "tracking_list": {
                "tracking": [
                    {
                        "fecha": "2026-01-01 10:00:00",
                        "codigo": "0",
                        "evento": "MANIFESTADA",
                    },
                    {
                        "fecha": "2026-01-02 10:00:00",
                        "codigo": "20",
                        "evento": "INCIDENCIA",
                    },
                ]
            },
            "digitalizaciones": {
                "digitalizacion": [
                    {"imagen": "https://example.com/no.pdf"},
                    {"imagen": "https://pods.gls-spain.es/pod.pdf"},
                ]
            },
        }
        response = mock.Mock(content=b"%PDF", status_code=200)
        response.raise_for_status.return_value = None
        with mock.patch(
            "odoo.addons.delivery_gls_asm.models.delivery_carrier.requests.get",
            return_value=response,
        ):
            self.carrier_gls_asm.gls_asm_tracking_state_update(self.picking)
        self.assertEqual(self.picking.gls_shipment_state, "closed")
        self.assertEqual(self.picking.delivery_state, "incident")
        self.assertTrue(self.picking.pod_file)
        service.tracking_exp["codestado"] = "22"
        service.tracking_exp["digitalizaciones"] = {
            "digitalizacion": {"imagen": "https://pods.gls-spain.es/pod.pdf"}
        }
        response.status_code = 500
        response.raise_for_status.side_effect = requests.HTTPError("unavailable")
        with mock.patch(
            "odoo.addons.delivery_gls_asm.models.delivery_carrier.requests.get",
            return_value=response,
        ):
            self.carrier_gls_asm.gls_asm_tracking_state_update(self.picking)
        self.assertFalse(self.picking.pod_error)
        service.tracking_exp["codestado"] = "91"
        service.tracking_exp["tracking_list"] = {
            "tracking": {
                "fecha": "2026-01-03 10:00:00",
                "codigo": "91",
                "evento": "INCIDENCIA",
            }
        }
        with mock.patch(
            "odoo.addons.delivery_gls_asm.models.delivery_carrier.requests.get",
            return_value=response,
        ):
            self.carrier_gls_asm.gls_asm_tracking_state_update(self.picking)
        self.assertTrue(self.picking.pod_error)
        service.tracking_error = True
        with self.assertRaises(UserError):
            self.carrier_gls_asm.gls_asm_tracking_state_update(self.picking)
        empty = self.picking.copy({"carrier_tracking_ref": False})
        self.carrier_gls_asm.gls_asm_tracking_state_update(empty)
        self.carrier_gls_asm.gls_asm_cancel_shipment(empty)

    def test_10_gls_pickup_edges_and_request_errors(self):
        service = self._patch_gls()
        self.carrier_gls_asm.gls_asm_service = "56"
        self.partner.country_id = self.env.ref("base.pt")
        service.pickup_clients = [
            SoapNode(
                Fecha="2026-01-01",
                Hora="09:00",
                Codigo="1",
                Descripcion="SOLICITADA",
            ),
            SoapNode(
                Fecha="2026-01-01",
                Hora="10:00",
                Codigo="0",
                Descripcion="EXTRA",
            ),
        ]
        self.picking.carrier_tracking_ref = "REC0000000000001"
        self.carrier_gls_asm.gls_asm_tracking_state_update(self.picking)
        self.assertEqual(self.picking.gls_pickup_state, "recorded")
        service.service_error = True
        with self.assertRaises(UserError):
            self.picking.gls_asm_send_pickup()
        service.service_error = False
        service.pickup_return = "-1"
        with self.assertRaises(UserError):
            self.picking.gls_asm_send_pickup()
        self.carrier_gls_asm.gls_asm_service = "37"
        service.service_error = True
        self.picking.name = "ODOO-0001"
        with self.assertRaises(UserError):
            self.carrier_gls_asm.gls_asm_send_shipping(self.picking)
        service.service_error = False
        service.shipment_return = "-1"
        with self.assertRaises(UserError):
            self.carrier_gls_asm.gls_asm_send_shipping(self.picking)
        service.shipment_return = "0"
        service.bad_references = True
        service.with_label = False
        with mute_logger("odoo.addons.delivery_gls_asm.models.delivery_carrier"):
            result = self.carrier_gls_asm.gls_asm_send_shipping(self.picking)
        self.assertEqual(result[0]["tracking_number"], "EXP0000000000001")
        self.assertFalse(self.picking.gls_asm_picking_ref)
        service.tracking_exp = {
            "codestado": "2",
            "estado": "EN TRANSITO",
            "tracking_list": {
                "tracking": {
                    "fecha": "2026-01-03 10:00:00",
                    "codigo": "2",
                    "evento": "EN TRANSITO",
                }
            },
        }
        self.picking.carrier_tracking_ref = "EXP0000000000001"
        with self.assertRaises(UserError):
            self.picking.cancel_shipment()

    def test_11_gls_soft_failures_and_phone(self):
        self._patch_gls()
        self.picking.name = "ODOO-0001"
        warehouse = self.picking.picking_type_id.warehouse_id
        warehouse.partner_id = False
        vals = self.carrier_gls_asm._prepare_gls_asm_shipping(self.picking)
        self.assertTrue(vals["remite_direccion"])
        request_path = (
            "odoo.addons.delivery_gls_asm.models.gls_asm_request.GlsAsmRequest"
        )
        with mock.patch(f"{request_path}._send_shipping", return_value={}):
            result = self.carrier_gls_asm.gls_asm_send_shipping(self.picking)
        self.assertFalse(result[0]["tracking_number"])
        self.carrier_gls_asm.gls_asm_service = "56"
        with mock.patch(f"{request_path}._send_pickup", return_value={"_return": -1}):
            result = self.carrier_gls_asm.gls_asm_send_pickup(self.picking)
        self.assertFalse(result[0]["tracking_number"])

        def _phone_format(record, number=None, **kwargs):
            return "34600111222"

        with mock.patch.object(
            type(self.carrier_gls_asm), "_phone_format", _phone_format, create=True
        ):
            self.assertEqual(
                self.carrier_gls_asm._sanitize_phone_gls("600111222"), "34600111222"
            )

    def test_12_gls_cancel_batch_with_rejection(self) -> None:
        service = self._patch_gls()
        self.picking.name = "ODOO-0001"
        self.picking.button_validate()
        rejected = self.picking.copy(
            {
                "carrier_id": self.carrier_gls_asm.id,
                "carrier_tracking_ref": "EXP0000000000002",
                "gls_asm_public_tracking_ref": "BAR0000000000002",
                "gls_asm_picking_ref": "INT0000000000002",
            }
        )
        cancel = service.Anula

        def cancel_by_reference(docIn=None) -> SoapNode:
            if rejected.carrier_tracking_ref in str(docIn):
                service.cancel_return = "-204"
                service.cancel_value = "Tiene tracking operativo"
            return cancel(docIn=docIn)

        with (
            mock.patch.object(service, "Anula", side_effect=cancel_by_reference),
            self.env.cr.savepoint(),
        ):
            (self.picking | rejected).cancel_shipment()

        cancellation_calls = [call[1] for call in service.calls if call[0] == "Anula"]
        self.assertEqual(len(cancellation_calls), 2)
        self.assertIn("EXP0000000000001", cancellation_calls[0])
        self.assertIn("EXP0000000000002", cancellation_calls[1])
        self.assertFalse(self.picking.carrier_tracking_ref)
        self.assertFalse(self.picking.gls_asm_public_tracking_ref)
        self.assertFalse(self.picking.gls_asm_picking_ref)
        self.assertEqual(self.picking.delivery_state, "canceled_shipment")
        self.assertEqual(rejected.carrier_tracking_ref, "EXP0000000000002")
        self.assertEqual(rejected.gls_asm_public_tracking_ref, "BAR0000000000002")
        self.assertEqual(rejected.gls_asm_picking_ref, "INT0000000000002")
        self.assertEqual(rejected.delivery_state, "shipping_recorded_in_carrier")
        rejected_messages = [message.body or "" for message in rejected.message_ids]
        self.assertTrue(
            any("Tiene tracking operativo" in body for body in rejected_messages)
        )
        self.assertFalse(
            any(
                "Shipment EXP0000000000002 cancelled" in body
                for body in rejected_messages
            )
        )

    def test_13_gls_cancel_mixed_carriers(self) -> None:
        fixed_carrier = self.carrier_gls_asm.copy({"delivery_type": "fixed"})
        other_pickings = self.picking.copy({"carrier_id": fixed_carrier.id})
        other_pickings |= self.picking.copy({"carrier_id": fixed_carrier.id})
        with mock.patch(
            "odoo.addons.stock_delivery.models.stock_picking.StockPicking"
            ".cancel_shipment",
            autospec=True,
        ) as cancel_shipment:
            (other_pickings | self.picking).cancel_shipment()
        self.assertEqual(
            cancel_shipment.call_args_list,
            [mock.call(self.picking), mock.call(other_pickings)],
        )
