# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from odoo.addons.point_of_sale.tests.common import TestPoSCommon


@tagged("post_install", "-at_install")
class TestPosOrderByDevice(TestPoSCommon):
    def setUp(self):
        super().setUp()
        self.config = self.basic_config
        self.config.write({"iface_l10n_es_simplified_invoice": True})
        self.product = self.create_product("Product", self.categ_basic, 10.0)
        # Enabled after opening: with the option on, open_ui requires a free
        # physical device.
        self.open_new_session()
        self.config.company_id.pos_sequence_by_device = True
        sequence = self.env["ir.sequence"].create(
            {
                "name": "Device sequence",
                "implementation": "standard",
                "prefix": "DEV/",
                "padding": 4,
            }
        )
        self.device = self.env["pos.device"].create(
            {
                "name": "Device",
                "sequence": sequence.id,
                "company_id": self.config.company_id.id,
            }
        )

    def _next(self, sequence):
        return sequence._get_current_sequence().number_next_actual

    def _with_device(self, order):
        order["data"]["device"] = {
            "id": self.device.id,
            "sequence": [self.device.sequence.id, self.device.sequence.name],
        }
        return order

    def _ticket(self, number):
        order = self.create_ui_order_data([(self.product, 1)])
        order["data"].update(
            {"l10n_es_unique_id": number, "is_l10n_es_simplified_invoice": True}
        )
        return self._with_device(order)

    def _invoice(self):
        order = self.create_ui_order_data(
            [(self.product, 1)], customer=self.customer, is_invoiced=True
        )
        return self._with_device(order)

    def _sync(self, order):
        res = self.env["pos.order"].create_from_ui([order])
        return self.env["pos.order"].browse(res[0]["id"])

    def test_invoiced_order_does_not_consume_device_number(self):
        before = self._next(self.device.sequence)
        order = self._sync(self._invoice())
        self.assertEqual(self._next(self.device.sequence), before)
        self.assertFalse(order.l10n_es_unique_id)
        self.assertEqual(order.pos_device_id, self.device)

    def test_simplified_order_consumes_device_number(self):
        before = self._next(self.device.sequence)
        order = self._sync(self._ticket("DEV/%04d" % before))
        self.assertEqual(self._next(self.device.sequence), before + 1)
        self.assertEqual(order.pos_device_id, self.device)

    def test_without_sequence_by_device_unchanged(self):
        self.config.company_id.pos_sequence_by_device = False
        before = self._next(self.device.sequence)
        order = self._sync(self._invoice())
        self.assertEqual(self._next(self.device.sequence), before)
        self.assertFalse(order.pos_device_id)
