# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
from unittest.mock import MagicMock, patch

import requests

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import Form, tagged
from odoo.tools import mute_logger

from odoo.addons.delivery_logista.models.logista_master_data import (
    build_logista_barcode_34,
    format_logista_barcode_reference,
    format_logista_code128_subsets,
    format_logista_main_reference,
    format_logista_postal_code_api,
    format_logista_postal_code_barcode,
    format_logista_postal_code_plaza,
    get_logista_country_id,
    sanitize_logista_email,
    sanitize_logista_nif,
    sanitize_logista_phone,
)
from odoo.addons.delivery_logista.models.logista_request import LogistaRequest

from .common import TestDeliveryLogistaCommon

REQUEST_PATH = "odoo.addons.delivery_logista.models.logista_request.requests.request"


@tagged("post_install", "-at_install")
class TestDeliveryLogista(TestDeliveryLogistaCommon):
    def _mock_response(self, status_code=200, json_data=None, text=""):
        resp = MagicMock()
        resp.status_code = status_code
        resp.text = text
        resp.content = b"{}" if json_data is not None else b""
        if json_data is not None:
            resp.json.return_value = json_data
        else:
            resp.json.side_effect = ValueError("No JSON")
        return resp

    def test_01_barcodes_subsets_and_sanitizers(self):
        """Verify exact 34-digit barcodes, Code 128 subsets, and field sanitizers
        against the official Logista Parcel v4 & CB-Programación specifications.
        """
        bc_v4 = build_logista_barcode_34(
            sector_code="0",
            service_id="1",
            postal_code="28021",
            origin_delegation_code="28",
            customer_code="125400",
            reference="10821",
            package_index=1,
            dest_country_code="ES",
            origin_country_code="ES",
        )
        self.assertEqual(len(bc_v4), 34)
        self.assertEqual(bc_v4, "010280212812540010821%000001010101")

        bc_cb = build_logista_barcode_34(
            sector_code="0",
            service_id="4",
            postal_code="41011",
            origin_delegation_code="08",
            customer_code="191410",
            reference="99002143",
            package_index=1,
            dest_country_code="ES",
            origin_country_code="ES",
        )
        self.assertEqual(bc_cb, "040410110819141099002143%001010101")
        self.assertEqual(
            format_logista_code128_subsets(bc_cb, mode="at"),
            "@C040410110819141099002143@B%0@C01010101",
        )
        zpl_cb = format_logista_code128_subsets(bc_cb, mode="zpl")
        self.assertEqual(zpl_cb, ">:040410110819141099002143>6%0>501010101")

        # Andorra ('AD500' -> '000500', country '03', API CountryId 'AN')
        self.assertEqual(get_logista_country_id("AD"), "AN")
        self.assertEqual(format_logista_postal_code_barcode("AD500", "AD"), "000500")
        self.assertEqual(format_logista_postal_code_api("AD500", "AD"), "00500")
        self.assertEqual(format_logista_postal_code_plaza("AD500", "AD"), "00500")
        bc_ad = build_logista_barcode_34(
            "0", "1", "AD500", "28", "125400", "123456789", 2, "AD", "ES"
        )
        self.assertEqual(bc_ad, "0100050028125400123456789002030103")

        # Portugal ('1501-201' / '15012012' -> '001501', country '02')
        self.assertEqual(format_logista_postal_code_barcode("15012012", "PT"), "001501")
        self.assertEqual(format_logista_postal_code_barcode("1501-201", "PT"), "001501")

        # Reference formatting, phone, email, NIF, and StockPackageType sync
        self.assertEqual(format_logista_main_reference("WH/OUT/00026"), "00026")
        self.assertEqual(format_logista_main_reference("WH/OUT/00112084"), "00112084")
        self.assertEqual(format_logista_barcode_reference("00112084"), "00112084%")
        self.assertEqual(format_logista_barcode_reference("AB12"), "AB12%0000")
        self.assertEqual(sanitize_logista_phone("+34 937 000 222 ext 45"), "937000222")
        self.assertEqual(sanitize_logista_phone("00351 210-111-222"), "210111222")
        self.assertEqual(
            sanitize_logista_email("Logistics <ops@example.com>; sec@example.com"),
            "ops@example.com",
        )
        self.assertEqual(sanitize_logista_nif("ES-B12345674"), "B12345674")
        self.assertEqual(self.package_type_parcel.shipper_package_code, "PARCEL")
        self.assertEqual(self.package_type_pallet.shipper_package_code, "PALLET")

    def test_02_rate_shipment_fixed_rules_and_availability(self):
        """Verify preconfigured data XML records, rate_shipment with fixed price,
        price rules, and destination filter.
        """
        default_carrier = self.env.ref("delivery_logista.delivery_carrier_logista_main")
        self.assertEqual(default_carrier.delivery_type, "logista")
        self.assertFalse(default_carrier.logista_api_token)
        self.assertFalse(default_carrier.logista_sender_code)
        self.assertEqual(
            default_carrier.logista_default_packaging_id,
            self.env.ref("delivery_logista.stock_package_type_logista_parcel"),
        )
        self.assertTrue(
            self.env.ref("delivery_logista.stock_package_type_logista_europallet")
        )
        self.assertTrue(
            self.env.ref("delivery_logista.stock_package_type_logista_half_pallet")
        )

        self.assertTrue(self.carrier.can_generate_return)
        self.assertTrue(self.carrier.supports_shipping_insurance)

        rate_res = self.carrier.logista_rate_shipment(self.sale_order)
        self.assertTrue(rate_res["success"])
        self.assertAlmostEqual(rate_res["price"], 8.50, places=2)

        self.env["delivery.price.rule"].create(
            {
                "carrier_id": self.carrier.id,
                "variable": "weight",
                "operator": ">=",
                "max_value": 1.0,
                "list_base_price": 12.0,
                "list_price": 0.50,
                "variable_factor": "weight",
            }
        )
        rule_res = self.carrier.logista_rate_shipment(self.sale_order)
        self.assertTrue(rule_res["success"])
        self.assertAlmostEqual(rule_res["price"], 22.0, places=2)

        self.carrier.country_ids = [(6, 0, [self.country_pt.id])]
        denied = self.carrier.logista_rate_shipment(self.sale_order)
        self.assertFalse(denied["success"])
        self.carrier.country_ids = [(5, 0, 0)]

    @patch(REQUEST_PATH)
    def test_03_send_shipping_payload_pdf_and_zpl_labels(self, mock_req):
        """Test POST /shipment/v1 payload generation, wsRepartoProductoPorPlazas
        lookup, 34-digit barcode assignment on packages, PDF QWeb rendering, and ZPL.
        """
        self.sale_order.client_order_ref = "PO-998877"
        self.picking.write(
            {
                "logista_arranged_delivery_date": fields.Date.from_string("2026-11-20"),
                "logista_delivery_note_action": "1",
                "logista_tight_flow": True,
                "logista_cod_amount": 150.25,
                "logista_insured_value": 500.00,
                "logista_customer_reference": "ALB00021",
                "logista_comments": "Deliver before 14:00 at loading dock 3",
            }
        )
        self.carrier.write(
            {
                "logista_epacking_enabled": True,
                "logista_epacking_mailing": True,
                "logista_epacking_printing": True,
            }
        )

        pkg_pallet = self.env["stock.quant.package"].create(
            {
                "name": "PAL-001",
                "package_type_id": self.package_type_pallet.id,
            }
        )
        pkg_parcel = self.env["stock.quant.package"].create(
            {
                "name": "BOX-001",
                "package_type_id": self.package_type_parcel.id,
            }
        )
        ml_first = self.picking.move_line_ids[0]
        ml_first.quantity = 6.0
        ml_first.result_package_id = pkg_pallet.id
        self.env["stock.move.line"].create(
            {
                "picking_id": self.picking.id,
                "move_id": self.picking.move_ids[0].id,
                "product_id": self.product.id,
                "product_uom_id": self.product.uom_id.id,
                "location_id": ml_first.location_id.id,
                "location_dest_id": ml_first.location_dest_id.id,
                "quantity": 4.0,
                "result_package_id": pkg_parcel.id,
            }
        )

        shipment_resp = self._mock_response(
            status_code=200,
            json_data={
                "Shipments": [
                    {
                        "SessionId": 2850457,
                        "ShipmentId": 36893429,
                        "References": ["ALB00021"],
                    }
                ]
            },
        )
        plaza_resp = self._mock_response(
            status_code=200,
            json_data={
                "zonaReparto": "304",
                "delegacion": "BARCELONA",
                "delegacionCB": "8",
                "delegacioncode": "080",
            },
        )
        mock_req.side_effect = [shipment_resp, plaza_resp]

        self.picking.send_to_shipper()

        first_call_kwargs = mock_req.call_args_list[0].kwargs
        self.assertEqual(
            first_call_kwargs["headers"]["Authorization"],
            "test-secret-token-9876543210",
        )
        sent_body = first_call_kwargs["json"]
        self.assertIsInstance(sent_body, list)
        shp = sent_body[0]["Shipment"]
        self.assertEqual(shp["ServiceId"], 1)
        self.assertEqual(shp["Sender"]["Code"], "280125400")
        self.assertEqual(shp["Consignee"]["CountryId"], "ES")
        self.assertEqual(shp["Consignee"]["PostalCode"], "08223")
        self.assertEqual(shp["Consignee"]["NIF"], "B12345674")
        self.assertEqual(shp["Consignee"]["Phone"], "937000222")
        self.assertEqual(shp["Consignee"]["Mail"], "receiving@example.com")
        self.assertEqual(shp["Consignee"]["CustomerCode"], "CUST-0099")
        self.assertEqual(shp["Notifications"]["Type"], 3)
        self.assertEqual(shp["Notifications"]["Phone"], "600123456")
        self.assertEqual(shp["MixShipment"], 1)
        self.assertEqual(shp["MixPalets"], 1)
        self.assertEqual(shp["MixPackages"], 1)
        self.assertEqual(shp["ControlPackages"], 2)
        self.assertEqual(shp["DeliveryNoteAction"], 1)
        self.assertEqual(shp["TightFlowService"], 1)
        self.assertEqual(shp["ArrangedDeliveryDate"], "2026-11-20")
        self.assertEqual(shp["CashOnDelivery"], 150.25)
        self.assertEqual(shp["InsuranceValue"], 500.00)
        self.assertTrue(shp["ePackingList"]["IsServiceEnabled"])
        self.assertEqual(shp["CustomerReferences"][0]["CustomerReference"], "ALB00021")
        self.assertTrue(shp["CustomerReferences"][0]["IsMain"])
        self.assertEqual(shp["CustomerReferences"][1]["CustomerReference"], "PO-998877")

        self.assertEqual(self.picking.carrier_tracking_ref, "36893429")
        self.assertEqual(self.picking.delivery_state, "shipping_recorded_in_carrier")
        self.assertEqual(self.picking.tracking_json.get("session_id"), "2850457")
        self.assertEqual(self.picking.tracking_json.get("delegacion"), "BARCELONA")
        self.assertEqual(self.picking.tracking_json.get("zona_reparto"), "304")
        self.assertEqual(len(pkg_pallet.logista_barcode), 34)
        self.assertEqual(len(pkg_parcel.logista_barcode), 34)

        pdf_att = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "stock.picking"),
                ("res_id", "=", self.picking.id),
                ("name", "=", "logista_label_36893429.pdf"),
            ]
        )
        self.assertTrue(pdf_att)

        # Reprint label in ZPL thermal format
        self.carrier.logista_label_format = "ZPL"
        zpl_att = self.picking.logista_get_label()
        self.assertTrue(zpl_att)
        self.assertTrue(zpl_att.name.endswith(".zpl"))
        zpl_content = base64.b64decode(zpl_att.datas).decode("utf-8")
        self.assertIn("^XA", zpl_content)
        self.assertIn("BARCELONA", zpl_content)
        self.assertIn("304", zpl_content)

    @mute_logger("odoo.addons.delivery_logista.models.logista_request")
    @patch(REQUEST_PATH)
    def test_04_error_formats_return_label_tracking_and_cancel(self, mock_req):
        """Test list & dict error responses (API v5 p.5-6), Bearer auth, return labels,
        plaza WS test action, tracking link, and local vs strict cancellation.
        """
        self.carrier.logista_auth_scheme = "bearer"

        mock_req.return_value = self._mock_response(
            status_code=400,
            json_data=[
                {
                    "Code": 783953403,
                    "Message": "Destination hub could not be discover",
                    "Date": "2026-11-17 10:40:38Z",
                    "CorrelationId": "adfd2618-8480-40ae-8474-b590778f398c",
                    "References": ["ALB00021"],
                }
            ],
        )
        with self.assertRaisesRegex(UserError, "783953403"):
            self.carrier.logista_send_shipping(self.picking)
        self.assertTrue(
            mock_req.call_args.kwargs["headers"]["Authorization"].startswith("Bearer ")
        )

        mock_req.return_value = self._mock_response(
            status_code=400,
            json_data={
                "Code": 6,
                "Message": "Specified token was not found",
                "CorrelationId": "f0b9c88b-bfec-4ad0-b113-edae554c5fe4",
                "References": [],
            },
        )
        with self.assertRaisesRegex(UserError, "Specified token was not found"):
            self.carrier.logista_send_shipping(self.picking)

        client = LogistaRequest(self.carrier)
        mock_req.side_effect = requests.exceptions.Timeout("Read timeout")
        with self.assertRaises(UserError):
            client.send_shipping(self.picking)
        mock_req.side_effect = requests.exceptions.ConnectionError("Offline")
        with self.assertRaises(UserError):
            client.send_shipping(self.picking)
        mock_req.side_effect = None

        ret_ship_resp = self._mock_response(
            status_code=200,
            json_data={
                "Shipments": [
                    {
                        "SessionId": 2850999,
                        "ShipmentId": 36899999,
                        "References": ["R00001"],
                    }
                ]
            },
        )
        plaza_resp = self._mock_response(
            status_code=200,
            json_data={
                "zonaReparto": "R1",
                "delegacion": "MADRID",
                "delegacionCB": "28",
                "delegacioncode": "280",
            },
        )
        mock_req.side_effect = [ret_ship_resp, plaza_resp]
        self.carrier.logista_get_return_label(self.picking)
        ret_att = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "stock.picking"),
                ("res_id", "=", self.picking.id),
                ("name", "ilike", "logista_return_36899999%"),
            ]
        )
        self.assertTrue(ret_att)

        mock_req.side_effect = None
        mock_req.return_value = plaza_resp
        notif_act = self.carrier.action_test_logista_plaza_ws()
        self.assertEqual(notif_act["params"]["type"], "success")

        self.carrier.logista_tracking_url = (
            "https://www.logistaparcel.com/seguimiento/?exp={tracking_ref}&cp={zip}"
        )
        self.picking.carrier_tracking_ref = "36893429"
        link = self.carrier.logista_get_tracking_link(self.picking)
        self.assertIn("36893429", link)
        self.assertIn("08223", link)

        self.carrier.logista_allow_local_cancel = False
        with self.assertRaises(UserError):
            self.picking.cancel_shipment()

        self.carrier.logista_allow_local_cancel = True
        self.picking.cancel_shipment()
        self.assertFalse(self.picking.carrier_tracking_ref)
        self.assertEqual(self.picking.delivery_state, "canceled_shipment")

    @patch(REQUEST_PATH)
    def test_05_ui_forms_pallets_incoterms_and_validations(self, mock_req):
        """Test Odoo 18 Form views, pure pallet shipments (1 pallet / 50 boxes),
        Incoterm mapping, automatic COD/Insurance from SO, and validation guards.
        """
        with Form(self.carrier) as c_form:
            c_form.logista_epacking_enabled = True
            c_form.logista_cash_on_delivery = True
            c_form.shipping_insurance = 50.0
        with Form(self.partner) as p_form:
            p_form.logista_freight_type = "D"
        with Form(self.package_type_parcel) as pt_form:
            pt_form.logista_package_kind = "parcel"
        with Form(self.picking) as pk_form:
            pk_form.logista_pallets_qty = 1
            pk_form.number_of_packages = 50

        self.picking.write(
            {
                "logista_cod_amount": 0.0,
                "logista_insured_value": 0.0,
                "logista_freight_type": False,
                "move_line_ids": [
                    (1, ml.id, {"result_package_id": False})
                    for ml in self.picking.move_line_ids
                ],
            }
        )
        self.sale_order.incoterm = self.env.ref("account.incoterm_EXW")

        client = LogistaRequest(self.carrier)
        payload, _ref, metrics = client._prepare_shipment_payload(self.picking)
        shp = payload[0]["Shipment"]
        self.assertEqual(shp["Packages"], 50)
        self.assertEqual(shp["ControlPackages"], 1)
        self.assertNotIn("MixShipment", shp)
        self.assertEqual(shp["FreightType"], "D")
        self.assertGreater(shp["InsuranceValue"], 0.0)
        self.assertGreater(shp["CashOnDelivery"], 0.0)
        self.assertEqual(metrics["unit_kinds"], ["pallet"])

        mock_req.return_value = self._mock_response(
            status_code=200,
            json_data={"zonaReparto": "304", "delegacion": "BARCELONA"},
        )
        items = self.picking._get_logista_label_items()
        self.assertEqual(len(items), 1)
        self.assertTrue(items[0]["is_pallet"])
        self.assertEqual(items[0]["packages"], 50)
        self.assertEqual(items[0]["control_packages"], 1)

        country_fr = self.env.ref("base.fr")
        fr_partner = self.env["res.partner"].create(
            {
                "name": "French Receiver",
                "street": "10 Rue de Rivoli",
                "city": "Paris",
                "zip": "75001",
                "country_id": country_fr.id,
            }
        )
        with self.assertRaises(UserError):
            client._validate_partner(fr_partner, picking=self.picking)

        self.carrier.logista_sender_code = False
        with self.assertRaises(UserError):
            client._prepare_shipment_payload(self.picking)
        self.carrier.logista_sender_code = "280125400"

        self.carrier.logista_api_token = False
        with self.assertRaises(UserError):
            client._get_headers(authenticated=True)
        self.carrier.logista_api_token = "test-secret-token-9876543210"

    @mute_logger("odoo.addons.delivery_logista.models.logista_request")
    @patch(REQUEST_PATH)
    def test_06_edge_cases_and_full_branch_coverage(self, mock_req):
        """Cover remaining sanitizers, UoM conversions, fallback branches,
        mixed shipments without packages, child contacts, and error paths.
        """
        # 1. Master data edge cases
        self.assertEqual(sanitize_logista_phone(""), "")
        self.assertEqual(sanitize_logista_phone("+44 20 7946 0958"), "2079460958")
        self.assertEqual(sanitize_logista_phone("0034912345678"), "912345678")
        self.assertEqual(sanitize_logista_phone("34912345678"), "912345678")
        self.assertEqual(sanitize_logista_email(""), "")
        self.assertEqual(sanitize_logista_email("not-an-email"), "")
        self.assertEqual(sanitize_logista_nif(""), "")
        self.assertEqual(format_logista_postal_code_api("", "ES"), "")
        self.assertEqual(format_logista_postal_code_api("1000-001", "PT"), "1000-001")
        self.assertEqual(format_logista_postal_code_plaza("", "ES"), "")
        self.assertEqual(format_logista_postal_code_plaza("1000-001", "PT"), "1000001")
        self.assertEqual(format_logista_main_reference(""), "0")
        self.assertEqual(format_logista_main_reference("ORD202600112084"), "600112084")
        self.assertEqual(format_logista_main_reference("ABCDEFGHIJKL"), "DEFGHIJKL")
        self.assertEqual(format_logista_code128_subsets(""), "")
        self.assertEqual(
            format_logista_code128_subsets("AB12CD34", mode="at"), "@BAB12CD34"
        )

        # 2. StockPackageType onchange and write sync
        pkg_new = self.env["stock.package.type"].new(
            {
                "package_carrier_type": "logista",
                "logista_package_kind": "pallet",
            }
        )
        pkg_new._onchange_logista_package_kind()
        self.assertEqual(pkg_new.shipper_package_code, "PALLET")

        dyn_pkg = self.env["stock.package.type"].create(
            {
                "name": "Logista Dynamic Type",
                "package_carrier_type": "logista",
                "logista_package_kind": "parcel",
            }
        )
        dyn_pkg.write({"logista_package_kind": "pallet"})
        self.assertEqual(dyn_pkg.shipper_package_code, "PALLET")
        other_pkg = self.env["stock.package.type"].create({"name": "Non Logista Box"})
        other_pkg._onchange_logista_package_kind()
        other_pkg.write({"logista_package_kind": "pallet"})

        # 3. Carrier barcode/delegation code fallbacks & empty attachment guard
        self.carrier.write(
            {
                "prod_environment": True,
                "logista_origin_delegation_code": False,
                "logista_customer_barcode_code": False,
                "logista_sender_code": "280125400",
            }
        )
        self.assertEqual(self.carrier._logista_get_origin_delegation_code(), "28")
        self.assertEqual(self.carrier._logista_get_customer_barcode_code(), "125400")
        self.carrier.logista_sender_code = False
        self.assertEqual(self.carrier._logista_get_origin_delegation_code(), "00")
        self.assertEqual(self.carrier._logista_get_customer_barcode_code(), "000000")
        self.carrier.write(
            {
                "prod_environment": False,
                "logista_sender_code": "280125400",
            }
        )
        self.assertFalse(
            self.carrier._logista_create_label_attachment(self.picking, b"", "123")
        )

        # Static tracking URL (without placeholders) & price rule mismatch error
        self.carrier.logista_tracking_url = "https://www.logistaparcel.com/"
        self.assertEqual(
            self.carrier.logista_get_tracking_link(self.picking),
            "https://www.logistaparcel.com/",
        )
        self.env["delivery.price.rule"].create(
            {
                "carrier_id": self.carrier.id,
                "variable": "weight",
                "operator": ">=",
                "max_value": 99999.0,
                "list_base_price": 50.0,
            }
        )
        unmatched_rate = self.carrier.logista_rate_shipment(self.sale_order)
        self.assertFalse(unmatched_rate["success"])
        self.carrier.price_rule_ids.unlink()

        # 4. LogistaRequest HTTP edge cases, UoM lb/ft³ conversions, & validations
        self.carrier.prod_environment = True
        prod_client = LogistaRequest(self.carrier)
        self.assertIn("clientes.integra2.es", prod_client.shipment_url)
        self.carrier.prod_environment = False

        client = LogistaRequest(self.carrier)
        self.assertEqual(
            client._mask_headers({"Authorization": "short"})["Authorization"], "***"
        )
        self.assertEqual(client._format_error_entry("raw_err"), "raw_err")

        mock_req.side_effect = requests.exceptions.Timeout("tmo")
        self.assertTrue(
            client._request(
                "GET", client.plaza_url, authenticated=False, raise_on_error=False
            )["_error"]
        )
        mock_req.side_effect = requests.exceptions.ConnectionError("conn")
        self.assertTrue(
            client._request(
                "GET", client.plaza_url, authenticated=False, raise_on_error=False
            )["_error"]
        )
        mock_req.side_effect = None

        mock_req.return_value = self._mock_response(status_code=200, text="PLAIN_OK")
        self.assertEqual(
            client._request("GET", client.plaza_url, authenticated=False)["raw"],
            "PLAIN_OK",
        )
        mock_req.return_value = self._mock_response(status_code=500, text="ISE")
        err_dict = client._request(
            "GET", client.plaza_url, authenticated=False, raise_on_error=False
        )
        self.assertTrue(err_dict["_error"])
        self.assertIn("500", err_dict["error_message"])

        # Empty / invalid shipment responses & plaza failure fallback
        mock_req.return_value = self._mock_response(status_code=200, json_data={})
        with self.assertRaises(UserError):
            client.send_shipping(self.picking)
        mock_req.return_value = self._mock_response(
            status_code=200, json_data={"Shipments": [{"ShipmentId": ""}]}
        )
        with self.assertRaises(UserError):
            client.send_shipping(self.picking)

        self.assertEqual(client.get_plaza_routing("ES", ""), {})
        mock_req.return_value = self._mock_response(status_code=503, text="Down")
        self.assertEqual(client.get_plaza_routing("ES", "28001"), {})
        with self.assertRaises(UserError):
            self.carrier.action_test_logista_plaza_ws()

        # UoM conversions (lbs & cubic feet) and partner validations
        self.assertEqual(client._convert_weight_to_kg(0), 0.0)
        self.assertEqual(client._convert_volume_to_m3(0), 0.0)
        icp = self.env["ir.config_parameter"].sudo()
        icp.set_param("product.weight_in_lbs", "1")
        icp.set_param("product.volume_in_cubic_feet", "1")
        self.assertLess(client._convert_weight_to_kg(10.0), 10.0)
        self.assertLess(client._convert_volume_to_m3(10.0), 10.0)
        icp.set_param("product.weight_in_lbs", "0")
        icp.set_param("product.volume_in_cubic_feet", "0")

        with self.assertRaises(UserError):
            client._validate_partner(self.env["res.partner"], picking=self.picking)
        incomplete = self.env["res.partner"].create(
            {"name": "Incomplete", "country_id": self.country_es.id}
        )
        with self.assertRaises(UserError):
            client._validate_partner(incomplete, picking=self.picking)

        # 5. Child contact with >40-char street, no phone/email notifications,
        # picking overrides, HTML note comments, mixed shipment without packages,
        # and auto return_label_on_delivery
        child_contact = self.env["res.partner"].create(
            {
                "name": "Warehouse Receiver Contact",
                "parent_id": self.partner.id,
                "type": "delivery",
                "street": (
                    "Calle Extraordinariamente Larga "
                    "Del Poligono Industrial Sur Numero 145"
                ),
                "street2": "Nave C",
                "city": "Terrassa",
                "zip": "08223",
                "country_id": self.country_es.id,
                "phone": False,
                "mobile": False,
                "email": False,
                "logista_freight_type": "D",
                "logista_notification_type": "1",
            }
        )
        consignee_data = client._prepare_consignee_data(child_contact)
        self.assertEqual(len(consignee_data["Address"]), 40)
        self.assertIn("Department", consignee_data)
        self.assertIsNone(client._prepare_notifications_data(child_contact))
        self.assertEqual(client._resolve_freight_type(partner=child_contact), "D")
        self.carrier.write(
            {"logista_auth_scheme": "bearer", "logista_api_token": "Bearer tok123"}
        )
        self.assertEqual(client._get_auth_header_value(), "Bearer tok123")
        self.carrier.write(
            {
                "logista_auth_scheme": "raw",
                "logista_api_token": "test-secret-token-9876543210",
            }
        )

        # Default pallet packaging fallback & mixed shipment without physical packages
        self.carrier.logista_default_packaging_id = self.package_type_pallet
        self.picking.write(
            {
                "partner_id": child_contact.id,
                "carrier_tracking_ref": False,
                "tracking_json": {},
                "number_of_packages": 0,
                "shipping_weight": 0.0,
                "weight": 0.0,
                "logista_pallets_qty": 0,
                "logista_loose_packages_qty": 0,
                "logista_service_id": "4",
                "logista_freight_type": "D",
                "logista_customer_reference": "REF99",
                "logista_comments": False,
                "note": "<p>Handle with care</p>",
            }
        )
        self.assertFalse(self.picking.logista_get_label())
        pallet_metrics = client._prepare_package_metrics(self.picking)
        self.assertEqual(pallet_metrics["unit_kinds"], ["pallet"])

        # Mixed pallet + loose parcels via integer fields & label fallback without plaza
        self.picking.write(
            {
                "logista_pallets_qty": 1,
                "logista_loose_packages_qty": 2,
            }
        )
        mock_req.return_value = self._mock_response(status_code=200, json_data={})
        lbl_items = self.picking._get_logista_label_items()
        self.assertEqual(len(lbl_items), 3)
        self.assertEqual(lbl_items[0]["main_reference"], "REF99")

        # Send shipping with number_of_packages=0 and return_label_on_delivery=True
        self.carrier.return_label_on_delivery = True
        ship_ok = self._mock_response(
            status_code=200,
            json_data={"Shipments": [{"SessionId": 11, "ShipmentId": 223344}]},
        )
        ret_ok = self._mock_response(
            status_code=200,
            json_data={"Shipments": [{"SessionId": 12, "ShipmentId": 223345}]},
        )
        plaza_empty = self._mock_response(status_code=200, json_data={})
        mock_req.side_effect = [ship_ok, plaza_empty, plaza_empty, ret_ok, plaza_empty]
        res_send = self.carrier.logista_send_shipping(self.picking)
        self.assertEqual(res_send[0]["tracking_number"], "223344")
        self.assertEqual(self.picking.number_of_packages, 3)
        self.carrier.return_label_on_delivery = False
