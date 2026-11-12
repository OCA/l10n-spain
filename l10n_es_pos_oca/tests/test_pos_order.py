# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from odoo.addons.point_of_sale.tests.common import TestPoSCommon


@tagged("post_install", "-at_install")
class TestL10nEsPosOcaOrder(TestPoSCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.config = cls.basic_config
        cls.config.write({"iface_l10n_es_simplified_invoice": True})

    def setUp(self):
        super().setUp()
        self.open_new_session()

    def _create_order(self, amount_total=10.0, to_invoice=False):
        return self.env["pos.order"].create(
            {
                "session_id": self.pos_session.id,
                "amount_total": amount_total,
                "amount_paid": amount_total,
                "amount_tax": 0.0,
                "amount_return": 0.0,
                "to_invoice": to_invoice,
            }
        )

    def test_write_paid_assigns_simplified_invoice_number(self):
        order = self._create_order()
        self.assertFalse(order.l10n_es_unique_id)
        order.write({"state": "paid"})
        self.assertTrue(order.l10n_es_unique_id)
        self.assertTrue(order.is_l10n_es_simplified_invoice)

    def test_write_paid_does_not_renumber_existing_order(self):
        """An order already numbered client side (classic POS flow) keeps
        its number and doesn't consume a second sequence number."""
        order = self._create_order()
        order.l10n_es_unique_id = "TEST-0001"
        order.is_l10n_es_simplified_invoice = True
        sequence = self.config.l10n_es_simplified_invoice_sequence_id
        next_before = sequence.number_next_actual
        order.write({"state": "paid"})
        self.assertEqual(order.l10n_es_unique_id, "TEST-0001")
        self.assertEqual(sequence.number_next_actual, next_before)

    def test_write_paid_above_limit_not_numbered(self):
        order = self._create_order(
            amount_total=self.config.l10n_es_simplified_invoice_limit + 100
        )
        order.write({"state": "paid"})
        self.assertFalse(order.l10n_es_unique_id)

    def test_write_paid_to_invoice_not_numbered(self):
        order = self._create_order(to_invoice=True)
        order.write({"state": "paid"})
        self.assertFalse(order.l10n_es_unique_id)
