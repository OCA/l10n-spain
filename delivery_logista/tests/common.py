# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon


class TestDeliveryLogistaCommon(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country_es = cls.env.ref("base.es")
        cls.country_pt = cls.env.ref("base.pt")
        cls.country_ad = cls.env.ref("base.ad")

        cls.state_madrid = cls.env["res.country.state"].search(
            [("country_id", "=", cls.country_es.id), ("code", "=", "M")],
            limit=1,
        ) or cls.env["res.country.state"].create(
            {
                "name": "Madrid",
                "code": "M",
                "country_id": cls.country_es.id,
            }
        )

        cls.wh_partner = cls.env["res.partner"].create(
            {
                "name": "Origin Warehouse Logistics Ltd.",
                "street": "Poligono Norte Calle Uno 10",
                "city": "Madrid",
                "zip": "28021",
                "state_id": cls.state_madrid.id,
                "country_id": cls.country_es.id,
                "phone": "+34 910 000 111",
                "email": "warehouse@example.com",
            }
        )
        cls.pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Logista Test Pricelist",
                "currency_id": cls.env.company.currency_id.id,
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Iberian Distribution Test Co.",
                "street": "Avenida Industrial 42 Nave B",
                "street2": "Muelle 3",
                "city": "Terrassa",
                "zip": "08223",
                "country_id": cls.country_es.id,
                "vat": "ESB12345674",
                "phone": "+34 937 000 222 ext 45",
                "mobile": "+34 600 123 456",
                "email": "Receiving Dept <receiving@example.com>, backup@example.com",
                "specific_property_product_pricelist": cls.pricelist.id,
                "logista_customer_code": "CUST-0099",
                "logista_notification_type": "3",
            }
        )

        cls.package_type_parcel = cls.env["stock.package.type"].create(
            {
                "name": "Logista Test Box",
                "package_carrier_type": "logista",
                "logista_package_kind": "parcel",
                "packaging_length": 40,
                "width": 30,
                "height": 30,
                "base_weight": 0.5,
                "max_weight": 30.0,
            }
        )
        cls.package_type_pallet = cls.env["stock.package.type"].create(
            {
                "name": "Logista Test Euro Pallet",
                "package_carrier_type": "logista",
                "logista_package_kind": "pallet",
                "packaging_length": 120,
                "width": 80,
                "height": 120,
                "base_weight": 20.0,
                "max_weight": 800.0,
            }
        )

        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Boxed Product 2kg",
                "type": "consu",
                "weight": 2.0,
                "volume": 0.015,
                "list_price": 25.0,
            }
        )
        cls.shipping_product = cls.env["product.product"].create(
            {
                "name": "Logista Shipping Service",
                "type": "service",
                "list_price": 8.50,
            }
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Logista Test Carrier",
                "delivery_type": "logista",
                "integration_level": "rate_and_ship",
                "product_id": cls.shipping_product.id,
                "prod_environment": False,
                "debug_logging": True,
                "logista_api_token": "test-secret-token-9876543210",
                "logista_auth_scheme": "raw",
                "logista_sender_code": "280125400",
                "logista_service_id": "1",
                "logista_sector_code": "0",
                "logista_freight_type": "P",
                "logista_origin_delegation_code": "28",
                "logista_customer_barcode_code": "125400",
                "logista_default_packaging_id": cls.package_type_parcel.id,
            }
        )

        order_form = Form(cls.env["sale.order"])
        order_form.partner_id = cls.partner
        with order_form.order_line.new() as line:
            line.product_id = cls.product
            line.product_uom_qty = 10.0
        cls.sale_order = order_form.save()
        cls.sale_order.pricelist_id = cls.pricelist
        cls.sale_order.carrier_id = cls.carrier
        cls.sale_order.action_confirm()
        cls.sale_order.warehouse_id.partner_id = cls.wh_partner
        cls.picking = cls.sale_order.picking_ids[0]
        cls.picking.carrier_id = cls.carrier
        cls.picking.move_ids.quantity = 10.0
