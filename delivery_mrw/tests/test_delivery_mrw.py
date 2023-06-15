import datetime

from odoo import _
from odoo.exceptions import UserError
from odoo.tests import Form, common


class TestDeliveryMRW(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        spain = cls.env["res.country"].search([("code", "=", "ES")])
        cls.env.company.partner_id.country_id = spain
        cls.env.company.external_report_layout_id = cls.env.ref(
            "web.external_layout_standard"
        )
        cls.shipping_product = cls.env["product.product"].create(
            {"type": "service", "name": "Test Shipping costs", "list_price": 10.0}
        )
        cls.carrier_mrw = cls.env.ref("delivery_mrw.mrw_carrier_test")
        cls.carrier_mrw.write(
            {
                "product_id": cls.shipping_product.id,
                "company_id": cls.env.company.id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {"type": "product", "name": "Test product"}
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Mr. Odoo & Co.",
                "city": "Madrid",
                "zip": "28001",
                "street": "Calle de La Rua, 3",
                "street2": "4-1",
                "country_id": spain.id,
            }
        )
        order_form = Form(cls.env["sale.order"].with_context(tracking_disable=True))
        order_form.partner_id = cls.partner
        order_form.date_order = datetime.datetime.today()
        with order_form.order_line.new() as line:
            line.product_id = cls.product
            line.product_uom_qty = 20.0
        cls.sale_order = order_form.save()
        cls.sale_order.carrier_id = cls.carrier_mrw.id
        cls.sale_order.action_confirm()
        cls.picking = cls.sale_order.picking_ids
        cls.picking.move_lines.quantity_done = 20

    def test_01_mrw_picking_confirm_simple(self):
        """The picking is confirmed and the shipping is recorded to MRW"""
        self.picking.name = "picking1"
        self.picking.button_validate()
        self.assertTrue(self.picking.carrier_tracking_ref)

    def test_02_mrw_manifest(self):
        """Manifest is created"""
        self.picking.name = "picking1"
        self.picking.button_validate()
        wizard = self.env["mrw.manifest.wizard"].create(
            {"carrier_id": self.carrier_mrw.id, "date_from": datetime.date.today()}
        )
        manifest_data = wizard.get_manifest()["data"]["deliveries"]
        self.assertEqual(
            manifest_data[-1]["carrier_tracking_ref"], self.picking.carrier_tracking_ref
        )

    def test_03_mrw_get_label(self):
        stock_picking = self.env["stock.picking"].create(
            {
                "delivery_type": "mrw",
                "carrier_tracking_ref": "MRW123456",
                "location_dest_id": 8,
                "location_id": 4,
                "picking_type_id": 1,
            }
        )

        stock_picking.mrw_get_label()

        self.assertTrue(stock_picking.message_ids, "No se creó ningún mensaje.")

    def test_04_prepare_html_address(self):
        mrw_address = {
            "street": "123 Main St",
            "city": "City",
            "zip": "12345",
            "country": "Country",
        }

        immediate_transfer = self.env["stock.immediate.transfer"]

        result = immediate_transfer._prepare_html_address(mrw_address)

        expected_result = (
            "<strong>street</strong>: 123 Main St <br>"
            "<strong>city</strong>: City <br>"
            "<strong>zip</strong>: 12345 <br>"
            "<strong>country</strong>: Country <br>"
        )
        self.assertEqual(result, expected_result)

    def test_05_get_manifest_no_deliveries(self):
        manifest_wizard = self.env["mrw.manifest.wizard"].create(
            {"date_from": "2023-06-14", "carrier_id": self.carrier_mrw.id}
        )

        with self.assertRaises(UserError) as error:
            manifest_wizard.get_manifest()

        self.assertEqual(
            error.exception.args[0],
            "It wasn't possible to get the manifest. Maybe there aren't"
            "deliveries for the selected date.",
        )

    def test_06_mrw_check_response(self):
        response = {
            "Estado": "1",
            "Mensaje": "Response message",
        }

        carrier = self.env["delivery.carrier"]
        result = carrier._mrw_check_response(response)

        expected_result = "Response message"
        self.assertEqual(result, expected_result)

    def test_07_street_missing(self):
        partner = self.env["res.partner"].create(
            {"name": "Test Partner"}
        )  # Sin valor para street

        with self.assertRaises(UserError) as context:
            self.env["delivery.carrier"].mrw_address(partner, False)

        expected_error_message = _("Couldn't find partner %s street") % partner.name
        self.assertEqual(context.exception.args[0], expected_error_message)

    def test_get_manifest_no_deliveries(self):
        manifest_wizard = self.env["mrw.manifest.wizard"].create(
            {
                "date_from": "2023-06-14",
            }
        )

        with self.assertRaises(UserError) as error:
            manifest_wizard.get_manifest()

        expected_error_message = _(
            "It wasn't possible to get the manifest. Maybe there aren't"
            "deliveries for the selected date."
        )
        self.assertMultiLineEqual(error.exception.args[0], expected_error_message)

    def test_prepare_mrw_tracking(self):
        carrier = self.env["delivery.carrier"].create(
            {
                "name": "test2",
                "product_id": 40,
                "mrw_username": "test_username",
                "mrw_password": "test_password",
                "mrw_api_language": "test_language",
                "mrw_api_filter_type": 0,
                "mrw_api_information_type": 0,
                "mrw_client_code": "test_client_code",
                "mrw_franquicia_code": "test_franquicia_code",
            }
        )

        picking = self.env["stock.picking"].create(
            {
                "carrier_tracking_ref": "test_tracking_ref",
                "location_dest_id": 8,
                "location_id": 4,
                "picking_type_id": 1,
            }
        )

        prepared_tracking = carrier._prepare_mrw_tracking(picking)

        expected_result = {
            "login": "test_username",
            "pass": "test_password",
            "codigoIdioma": "test_language",
            "tipoFiltro": 0,
            "valorFiltroDesde": "test_tracking_ref",
            "valorFiltroHasta": "test_tracking_ref",
            "fechaDesde": "",
            "fechaHasta": "",
            "tipoInformacion": 0,
            "codigoAbonado": "test_client_code",
            "codigoFranquicia": "test_franquicia_code",
        }
        self.assertEqual(prepared_tracking, expected_result)
