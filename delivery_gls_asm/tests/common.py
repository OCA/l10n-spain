# Copyright 2026 Studio73 - Pablo Cortés <pablo.cortes@studio73.es>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
# Copyright 2020 Tecnativa - David Vidal
# Copyright 2021 Tecnativa - Víctor Martínez

from unittest import mock

from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon

from .gls_soap import REQUEST_PATH, FakeGlsClient, FakeGlsService, asdict


class DeliveryGlsAsmCommon(BaseCommon):
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
