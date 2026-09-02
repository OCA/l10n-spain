# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from unittest.mock import MagicMock, patch

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.base.tests.common import BaseCommon
from odoo.addons.queue_job.tests.common import trap_jobs


@tagged("post_install", "-at_install")
class TestSaleInsuranceCaser(BaseCommon):
    # Tarification → Lot Assignment → Policy Issuance
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_caser_config()
        cls._setup_addresses()
        cls._setup_products()
        cls._setup_insurance_products()

    @classmethod
    def _setup_caser_config(cls):
        config_params = {
            "sale_insurance_caser.username": "TEST_USER",
            "sale_insurance_caser.is_production": "False",
            "sale_insurance_caser.agency_code": "9999",
            "sale_insurance_caser.agent_code": "9999999",
            "sale_insurance_caser.sica_code": "9999",
        }
        for key, value in config_params.items():
            cls.env["ir.config_parameter"].sudo().set_param(key, value)

    @classmethod
    def _setup_addresses(cls):
        cls.env.company.write(
            {
                "street": "Test Company Street 123",
                "city": "Test City",
                "zip": "03001",
                "state_id": cls.env.ref("base.state_es_a").id,
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Customer",
                "vat": "ES12345678Z",
                "street": "Test Street 456",
                "city": "Test Town",
                "zip": "29001",
                "phone": "600000000",
                "email": "test@example.com",
                "state_id": cls.env.ref("base.state_es_ma").id,
            }
        )

    @classmethod
    def _setup_products(cls):
        cls.brand = cls.env["product.brand"].create(
            {
                "name": "SAMSUNG",
                "caser_mobile_code": "479",
                "caser_tablet_code": "396",
            }
        )
        cls.phone_category = cls.env["product.category"].create(
            {
                "name": "Test Phone Category",
                "caser_asset_type": "200021",
                "caser_protocol": "61680",
            }
        )
        cls.tablet_category = cls.env["product.category"].create(
            {
                "name": "Test Tablet Category",
                "caser_asset_type": "262",
                "caser_protocol": "61681",
            }
        )
        cls.phone_product = cls.env["product.product"].create(
            {
                "name": "Samsung Galaxy S21",
                "type": "consu",
                "is_storable": True,
                "list_price": 500.0,
                "tracking": "serial",
                "product_brand_id": cls.brand.id,
                "categ_id": cls.phone_category.id,
            }
        )
        cls.tablet_product = cls.env["product.product"].create(
            {
                "name": "Samsung Galaxy Tab",
                "type": "consu",
                "is_storable": True,
                "list_price": 300.0,
                "tracking": "serial",
                "product_brand_id": cls.brand.id,
                "categ_id": cls.tablet_category.id,
            }
        )

    @classmethod
    def _setup_insurance_products(cls):
        price_range_5 = cls.env.ref("sale_insurance_caser.caser_price_range_mobile_5")
        product_5 = price_range_5._create_or_update_insurance_product(
            price_range_5.insurance_price
        )
        price_range_5.write({"product_id": product_5.id})
        cls.tablet_price_range = cls.env.ref(
            "sale_insurance_caser.caser_price_range_tablet_3"
        )
        cls.tablet_price_range.product_id = (
            cls.tablet_price_range._create_or_update_insurance_product(
                cls.tablet_price_range.insurance_price
            ).id
        )

    def _create_sale_order_with_insurance(self, lines):
        return self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": lines,
            }
        )

    def _create_stock_with_lot(self, product, lot_name, quantity=1.0):
        lot = self.env["stock.lot"].create(
            {
                "name": lot_name,
                "product_id": product.id,
                "company_id": self.env.company.id,
            }
        )
        self.env["stock.quant"]._update_available_quantity(
            product, self.env.ref("stock.stock_location_stock"), quantity, lot_id=lot
        )
        return lot

    def test_01_lot_assignment_by_price_range(self):
        # Verify lots are assigned to insurance lines matching price range
        phone_lots = [
            self._create_stock_with_lot(self.phone_product, "PHONE_001"),
            self._create_stock_with_lot(self.phone_product, "PHONE_002"),
        ]
        tablet_lot = self._create_stock_with_lot(self.tablet_product, "TABLET_001")
        order = self._create_sale_order_with_insurance(
            [
                Command.create(
                    {
                        "product_id": self.phone_product.id,
                        "product_uom_qty": 2,
                        "price_unit": 500.0,
                        "caser_insure_quantity": 2,
                    }
                ),
                Command.create(
                    {
                        "product_id": self.tablet_product.id,
                        "product_uom_qty": 1,
                        "price_unit": 300.0,
                        "caser_insure_quantity": 1,
                    }
                ),
            ]
        )
        insurance_lines = order.order_line.filtered(
            lambda line: line.is_caser_insurance
        )
        self.assertEqual(len(insurance_lines), 3)
        phone_insurance = insurance_lines.filtered(
            lambda line: "CASER_RANGE_200021_5" in line.product_id.default_code
        )
        self.assertEqual(len(phone_insurance), 2)
        tablet_insurance = insurance_lines.filtered(
            lambda line: "CASER_RANGE_262_3" in line.product_id.default_code
        )
        self.assertEqual(len(tablet_insurance), 1)
        order.action_confirm()
        picking = order.picking_ids[0]
        picking.action_assign()
        price_range_5 = self.env.ref("sale_insurance_caser.caser_price_range_mobile_5")
        range_price_map = {
            self.tablet_price_range.code: self.tablet_price_range.insurance_price,
            price_range_5.code: price_range_5.insurance_price,
        }

        def _mock_response(endpoint, soap_envelope):
            price = next(
                (
                    p
                    for c, p in range_price_map.items()
                    if f"<CBO_ELDO_PR_3825>{c}</CBO_ELDO_PR_3825>" in soap_envelope
                ),
                0.0,
            )
            r = MagicMock()
            r.status_code = 200
            r.text = (
                '<?xml version="1.0" encoding="UTF-8"?>'
                "<SERVICIO>"
                "<P_NPOLPRO>POL123</P_NPOLPRO>"
                "<P_TEXTO>OK</P_TEXTO>"
                f"<PRIMA_itotre>{price}</PRIMA_itotre>"
                "</SERVICIO>"
            )
            return r

        with trap_jobs() as trap:
            with patch(
                "odoo.addons.sale_insurance_caser.models.caser_api_mixin.CaserApiMixin._send_caser_soap_request",
                side_effect=_mock_response,
            ):
                picking.button_validate()
                trap.perform_enqueued_jobs()
        # Verify lots were assigned to correct insurance lines after validation
        phone_assigned = insurance_lines.filtered(
            lambda line: line.caser_lot_id.product_id == self.phone_product
        )
        self.assertEqual(len(phone_assigned), 2)
        for lot in phone_lots:
            self.assertIn(lot, phone_assigned.mapped("caser_lot_id"))
        tablet_assigned = insurance_lines.filtered(
            lambda line: line.caser_lot_id.product_id == self.tablet_product
        )
        self.assertEqual(len(tablet_assigned), 1)
        self.assertEqual(tablet_assigned.caser_lot_id, tablet_lot)

    def test_02_tarification_flow(self):
        # Test tarification request (P_COPER=00) and price updates
        price_ranges = self.env["caser.price.range"].search(
            [("code", "in", ["3", "4"])], limit=2
        )
        self.assertTrue(price_ranges)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
<SERVICIO>
    <P_TEXTO>OK</P_TEXTO>
    <P_LISTRECIBOS_LISTABEANS>
        <REPETIDO>
            <PRIMA_ipriom>40.00</PRIMA_ipriom>
            <PRIMA_itotre>48.40</PRIMA_itotre>
        </REPETIDO>
        <REPETIDO>
            <PRIMA_ipriom>41.00</PRIMA_ipriom>
            <PRIMA_itotre>49.61</PRIMA_itotre>
        </REPETIDO>
        <REPETIDO>
            <PRIMA_ipriom>42.00</PRIMA_ipriom>
            <PRIMA_itotre>50.82</PRIMA_itotre>
        </REPETIDO>
        <REPETIDO>
            <PRIMA_ipriom>43.00</PRIMA_ipriom>
            <PRIMA_itotre>52.03</PRIMA_itotre>
        </REPETIDO>
    </P_LISTRECIBOS_LISTABEANS>
</SERVICIO>"""
        with patch(
            "odoo.addons.sale_insurance_caser.models.caser_api_mixin.CaserApiMixin._send_caser_soap_request",
            return_value=mock_response,
        ) as mock_request:
            price_ranges.action_get_tarification_prices()
            self.assertEqual(mock_request.call_count, len(price_ranges))
            xml_sent = mock_request.call_args_list[0][0][1]
            self.assertIn("<P_COPER>00</P_COPER>", xml_sent)
            self.assertIn("<P_NPRODUC>2419</P_NPRODUC>", xml_sent)
            self.assertIn("soapenv:Envelope", xml_sent)
        for price_range in price_ranges:
            self.assertGreater(price_range.insurance_price, 0)
            self.assertTrue(price_range.last_tarification_date)
            product = price_range.product_id
            self.assertTrue(product)
            self.assertEqual(product.list_price, price_range.insurance_price)
            self.assertIn("CASER_RANGE_", product.default_code)
            self.assertEqual(product.type, "service")
            self.assertEqual(len(product.taxes_id), 0)

    def test_03_policy_issuance_flow(self):
        # Test policy issuance request (P_COPER=03) and response handling
        lot = self._create_stock_with_lot(self.phone_product, "SN123456789")
        order = self._create_sale_order_with_insurance(
            [
                Command.create(
                    {
                        "product_id": self.phone_product.id,
                        "product_uom_qty": 1,
                        "price_unit": 500.0,
                        "caser_insure_quantity": 1,
                    }
                ),
            ]
        )
        order.action_confirm()
        picking = order.picking_ids[0]
        picking.action_assign()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
<SERVICIO>
    <P_NPOLPRO>POL987654321</P_NPOLPRO>
    <P_TEXTO>OK</P_TEXTO>
    <P_DONDE>OK</P_DONDE>
    <PRIMA_itotre>76.27</PRIMA_itotre>
</SERVICIO>"""
        with trap_jobs() as trap:
            with patch(
                "odoo.addons.sale_insurance_caser.models.caser_api_mixin.CaserApiMixin._send_caser_soap_request",
                return_value=mock_response,
            ) as mock_request:
                picking.button_validate()
                trap.perform_enqueued_jobs()
                self.assertEqual(mock_request.call_count, 1)
                xml_sent = mock_request.call_args[0][1]
                self.assertIn("soapenv:Envelope", xml_sent)
                self.assertIn("<![CDATA[", xml_sent)
                self.assertIn("<P_COPER>03</P_COPER>", xml_sent)
                self.assertIn("<P_EMITIR>S</P_EMITIR>", xml_sent)
                self.assertIn("SN123456789", xml_sent)
                self.assertIn("<P_NSPARAME>61680</P_NSPARAME>", xml_sent)
                self.assertIn("12345678", xml_sent)
                self.assertIn("Test Town", xml_sent)
                self.assertIn("<CBO_ELDO_PR_3825>5</CBO_ELDO_PR_3825>", xml_sent)
        insurance_line = order.order_line.filtered(
            lambda line: line.is_caser_insurance
        )[0]
        self.assertEqual(insurance_line.caser_lot_id, lot)
        if insurance_line.caser_error_message:
            self.fail(f"Insurance request failed: {insurance_line.caser_error_message}")
        self.assertEqual(insurance_line.caser_policy_number, "POL987654321")
        self.assertEqual(insurance_line.caser_insurance_price, 76.27)
        self.assertTrue(insurance_line.caser_request_xml)
        self.assertTrue(insurance_line.caser_response_xml)
        self.assertFalse(insurance_line.caser_error_message)
        # Once issued, the line must not be selected nor sent again (e.g. a
        # backorder validation or a requeued job would duplicate the policy).
        self.assertFalse(picking._get_insurance_lines_with_lots())
        with patch(
            "odoo.addons.sale_insurance_caser.models.caser_api_mixin.CaserApiMixin._send_caser_soap_request",
            return_value=mock_response,
        ) as mock_resend:
            picking._send_caser_insurance_request(insurance_line)
        self.assertEqual(mock_resend.call_count, 0)
        self.assertEqual(insurance_line.caser_policy_number, "POL987654321")

    def test_05_order_insurance_state(self):
        order = self._create_sale_order_with_insurance(
            [
                Command.create(
                    {
                        "product_id": self.phone_product.id,
                        "product_uom_qty": 1,
                        "price_unit": 500.0,
                        "caser_insure_quantity": 1,
                    }
                ),
            ]
        )
        ins = order.order_line.filtered("is_caser_insurance")
        self.assertTrue(ins)
        self.assertEqual(order.caser_insurance_state, "to_send")
        self.assertFalse(order.caser_has_error)
        ins.caser_policy_number = "POLX"
        self.assertEqual(order.caser_insurance_state, "done")
        ins.caser_error_message = "Boom"
        self.assertEqual(order.caser_insurance_state, "error")
        self.assertTrue(order.caser_has_error)
        self.assertIn("Boom", order.caser_error)
        order2 = self._create_sale_order_with_insurance(
            [
                Command.create(
                    {
                        "product_id": self.phone_product.id,
                        "product_uom_qty": 1,
                        "price_unit": 500.0,
                    }
                ),
            ]
        )
        self.assertEqual(order2.caser_insurance_state, "no")
        self.assertFalse(order2.caser_has_error)

    def test_04_error_handling(self):
        # Test error handling for API errors and price mismatche
        self._create_stock_with_lot(self.phone_product, "SN_ERROR_001")
        order1 = self._create_sale_order_with_insurance(
            [
                Command.create(
                    {
                        "product_id": self.phone_product.id,
                        "product_uom_qty": 1,
                        "price_unit": 500.0,
                        "caser_insure_quantity": 1,
                    }
                ),
            ]
        )
        order1.action_confirm()
        picking1 = order1.picking_ids[0]
        picking1.action_assign()

        mock_error = MagicMock()
        mock_error.status_code = 200
        mock_error.text = """<?xml version="1.0" encoding="UTF-8"?>
<SERVICIO>
    <P_DONDE>NOK</P_DONDE>
    <P_TEXTO>Invalid customer data</P_TEXTO>
</SERVICIO>"""
        with trap_jobs() as trap:
            with patch(
                "odoo.addons.sale_insurance_caser.models.caser_api_mixin.CaserApiMixin._send_caser_soap_request",
                return_value=mock_error,
            ):
                picking1.button_validate()
                with self.assertRaises(UserError) as cm:
                    trap.perform_enqueued_jobs()
        self.assertIn("Invalid customer data", str(cm.exception))
        # Test price mismatch
        self._create_stock_with_lot(self.phone_product, "SN_PRICE_002")
        order2 = self._create_sale_order_with_insurance(
            [
                Command.create(
                    {
                        "product_id": self.phone_product.id,
                        "product_uom_qty": 1,
                        "price_unit": 500.0,
                        "caser_insure_quantity": 1,
                    }
                ),
            ]
        )
        order2.action_confirm()
        picking2 = order2.picking_ids[0]
        picking2.action_assign()
        mock_price_mismatch = MagicMock()
        mock_price_mismatch.status_code = 200
        mock_price_mismatch.text = """<?xml version="1.0" encoding="UTF-8"?>
<SERVICIO>
    <P_NPOLPRO>POL999</P_NPOLPRO>
    <P_TEXTO>OK</P_TEXTO>
    <P_DONDE>OK</P_DONDE>
    <PRIMA_itotre>999.99</PRIMA_itotre>
</SERVICIO>"""
        with trap_jobs() as trap:
            with patch(
                "odoo.addons.sale_insurance_caser.models.caser_api_mixin.CaserApiMixin._send_caser_soap_request",
                return_value=mock_price_mismatch,
            ):
                picking2.button_validate()
                trap.perform_enqueued_jobs()
        # Price mismatch must NOT abort: policy and price are persisted and
        # the discrepancy is logged on the line + order chatter.
        insurance_line = order2.order_line.filtered(
            lambda line: line.is_caser_insurance
        )[0]
        self.assertEqual(insurance_line.caser_policy_number, "POL999")
        self.assertEqual(insurance_line.caser_insurance_price, 999.99)
        self.assertTrue(insurance_line.caser_response_xml)
        self.assertIn("Price mismatch", insurance_line.caser_error_message or "")
        self.assertTrue(
            order2.message_ids.filtered(lambda m: "Price mismatch" in (m.body or ""))
        )
