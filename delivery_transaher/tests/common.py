# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64

from odoo.tests import Form, TransactionCase

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


class TestDeliveryTransaherCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))

        cls.country_es = cls.env.ref("base.es")
        cls.country_pt = cls.env.ref("base.pt")
        cls.state_madrid = cls.env["res.country.state"].search(
            [("country_id", "=", cls.country_es.id), ("code", "=", "M")],
            limit=1,
        )
        if not cls.state_madrid:
            cls.state_madrid = cls.env["res.country.state"].create(
                {
                    "name": "Madrid",
                    "code": "M",
                    "country_id": cls.country_es.id,
                }
            )

        cls.wh_partner = cls.env["res.partner"].create(
            {
                "name": "Agruconf Central Logistics S.L.",
                "street": "Poligono Industrial Norte Calle 12",
                "city": "Valencia",
                "zip": "46001",
                "country_id": cls.country_es.id,
                "phone": "+34960000111",
                "email": "logistica@agruconf.es",
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Manuel Fernandez Garcia S.L.",
                "street": "Ortega y Gasset 75",
                "city": "Madrid",
                "zip": "28006",
                "state_id": cls.state_madrid.id,
                "country_id": cls.country_es.id,
                "phone": "910001122",
                "mobile": "600123456",
                "email": "manuel@example.com",
                "transaher_portes_default": "1",
                "transaher_delivery_notes": (
                    "Entregar en horario de mañana de 09:00 a 14:00 en muelle trasero"
                ),
            }
        )

        cls.package_type_box = cls.env["stock.package.type"].create(
            {
                "name": "Transaher Test Box 40x30x30",
                "package_carrier_type": "transaher",
                "transaher_packaging_code": "BUL",
                "packaging_length": 400,
                "width": 300,
                "height": 300,
                "base_weight": 0.5,
                "max_weight": 30.0,
            }
        )

        cls.product = cls.env["product.product"].create(
            {
                "name": "Artisan Chocolate Assortment 2.5kg",
                "type": "consu",
                "weight": 2.5,
                "list_price": 32.0,
                "taxes_id": [(5, 0, 0)],
                "dimensional_uom_id": cls.env.ref("uom.product_uom_meter").id,
                "product_length": 0.50,
                "product_width": 0.30,
                "product_height": 0.20,
            }
        )
        cls.delivery_product = cls.env["product.product"].create(
            {
                "name": "Transaher Freight Service Test",
                "type": "service",
                "list_price": 0.0,
            }
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Transaher Test Carrier",
                "delivery_type": "transaher",
                "integration_level": "rate_and_ship",
                "product_id": cls.delivery_product.id,
                "prod_environment": False,
                "debug_logging": True,
                "transaher_client_code_test": "12345",
                "transaher_password_test": "test-secret-psw",
                "transaher_client_code_prod": "99999",
                "transaher_password_prod": "prod-secret-psw",
                "transaher_holding": 0,
                "transaher_seccion": 10,
                "transaher_centro_cod": 461,
                "transaher_centro_label": "461 VALENCIA",
                "transaher_protocolo": 20,
                "transaher_portes": "1",
                "transaher_default_package_type_id": cls.package_type_box.id,
                "transaher_default_packaging_code": "BUL",
                "transaher_label_mode": "ws_with_fallback",
                "transaher_bultos_tag_mode": "reprint_all",
                "transaher_volumetric_factor": 250.0,
                "transaher_fuel_surcharge_pct": 5.0,
                "transaher_cod_surcharge_pct": 2.0,
                "transaher_insurance_surcharge_pct": 1.0,
            }
        )
        cls.tariff_rule = cls.env["transaher.tariff.rule"].create(
            {
                "name": "Spain Mainland Excess Kg",
                "carrier_id": cls.carrier.id,
                "sequence": 10,
                "country_ids": [(6, 0, [cls.country_es.id])],
                "state_ids": [(6, 0, [cls.state_madrid.id])],
                "zip_prefixes": "28, 46",
                "rate_type": "per_excess_kg",
                "base_price": 12.0,
                "included_weight": 20.0,
                "price_per_kg": 0.25,
                "min_charge": 12.0,
                "fuel_surcharge_pct": 5.0,
            }
        )

        cls.sample_pdf_b64 = base64.b64encode(
            b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF"
        ).decode("ascii")

        order_form = Form(cls.env["sale.order"].with_context(tracking_disable=True))
        order_form.partner_id = cls.partner
        with order_form.order_line.new() as line:
            line.product_id = cls.product
            line.product_uom_qty = 10.0
            line.price_unit = 32.0
        cls.sale_order = order_form.save()
        cls.sale_order.client_order_ref = "REF-01"
        cls.sale_order.carrier_id = cls.carrier
        cls.sale_order.action_confirm()
        cls.sale_order.warehouse_id.partner_id = cls.wh_partner
        cls.picking = cls.sale_order.picking_ids[0]
        cls.picking.carrier_id = cls.carrier
        cls.picking.move_ids.quantity = 10.0
