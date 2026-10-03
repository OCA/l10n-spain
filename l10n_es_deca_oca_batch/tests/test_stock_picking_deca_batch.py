# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestStockPickingDecaBatch(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )

        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "consu",
            }
        )

        cls.location_customer = cls.env.ref("stock.stock_location_customers")
        cls.location_stock = cls.env.ref("stock.stock_location_stock")
        cls.picking_type_out = cls.env.ref("stock.picking_type_out")

        cls.picking = cls.env["stock.picking"].create(
            {
                "partner_id": cls.partner.id,
                "picking_type_id": cls.picking_type_out.id,
                "location_id": cls.location_stock.id,
                "location_dest_id": cls.location_customer.id,
            }
        )

        cls.batch = cls.env["stock.picking.batch"].create(
            {
                "name": "Batch Test",
                "picking_type_id": cls.picking_type_out.id,
            }
        )

        cls.picking.batch_id = cls.batch.id

    def test_01_report_batch(self):
        """Test report printing for batch"""
        report = self.env.ref("l10n_es_deca_oca_batch.action_report_deca_batch")
        self.assertTrue(report)
