# Copyright 2021 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import exceptions
from odoo.tests.common import tagged

from .common import TestL10nEsTicketBAIPoSCommon


@tagged("-at_install", "post_install")
class TestL10nEsTicketBAIPoSOrder(TestL10nEsTicketBAIPoSCommon):
    def setUp(self):
        super().setUp()

    def test_create_pos_order_from_ui(self):
        self.pos_config.open_session_cb()
        pos_order = self.create_pos_order_from_ui(self.account_billing)
        self.assertEqual("paid", pos_order.state)
        self.assertEqual("pending", pos_order.tbai_invoice_id.state)

    def test_create_pos_orders_from_ui(self):
        self.pos_config.open_session_cb()
        pos_order = self.create_pos_order_from_ui(self.account_billing)
        self.assertEqual("paid", pos_order.state)
        self.assertEqual("pending", pos_order.tbai_invoice_id.state)
        pos_order2 = self.create_pos_order_from_ui2(self.account_billing)
        self.assertEqual("paid", pos_order2.state)
        self.assertEqual("pending", pos_order2.tbai_invoice_id.state)

    def test_create_invoice_from_ui(self):
        self.pos_config.open_session_cb()
        pos_order = self.create_pos_order_from_ui(
            self.account_billing,
            partner_id=self.partner.id,
            fp=self.fiscal_position_national,
            to_invoice=True,
        )
        self.assertEqual("invoiced", pos_order.state)
        self.assertFalse(pos_order.tbai_invoice_id)
        self.assertEqual("posted", pos_order.account_move.state)
        self.assertEqual("pending", pos_order.account_move.tbai_invoice_id.state)

    def test_create_invoice_from_ui_partner(self):
        self.pos_config.open_session_cb()
        pos_order = self.create_pos_order_from_ui(
            self.account_billing, partner_id=self.partner.id, to_invoice=True
        )
        self.assertEqual("invoiced", pos_order.state)
        self.assertFalse(pos_order.tbai_invoice_id)
        self.assertEqual("posted", pos_order.account_move.state)
        self.assertEqual("pending", pos_order.account_move.tbai_invoice_id.state)

    def test_create_pos_order(self):
        self.pos_config.open_session_cb()
        pos_order = self.create_pos_order(self.account_billing.id)
        self.assertFalse(pos_order.tbai_invoice_id)
        pos_order.sudo()._tbai_build_invoice()
        self.assertEqual("paid", pos_order.state)
        self.assertEqual("pending", pos_order.tbai_invoice_id.state)

    def test_create_invoice_from_pos_order(self):
        self.pos_config.open_session_cb()
        pos_order = self.create_pos_order(self.account_billing.id)
        self.assertFalse(pos_order.tbai_invoice_id)
        pos_order.sudo()._tbai_build_invoice()
        self.assertEqual("paid", pos_order.state)
        self.assertEqual("pending", pos_order.tbai_invoice_id.state)
        pos_order.sudo().with_context(
            with_company=pos_order.company_id.id
        ).action_pos_order_invoice()
        self.assertEqual("invoiced", pos_order.state)
        self.assertEqual("posted", pos_order.account_move.state)
        self.assertTrue(pos_order.account_move.tbai_substitute_simplified_invoice)
        self.assertEqual("pending", pos_order.account_move.tbai_invoice_id.state)

    def test_create_refund_invoice_from_pos_order(self):
        self.pos_config.open_session_cb()
        pos_order = self.create_pos_order(self.account_billing.id)
        self.assertFalse(pos_order.tbai_invoice_id)
        pos_order.account_move._post(True)
        pos_order.sudo()._tbai_build_invoice()
        self.assertEqual("paid", pos_order.state)
        self.assertEqual("pending", pos_order.tbai_invoice_id.state)
        pos_order.sudo().with_context(
            with_company=pos_order.company_id.id
        ).action_pos_order_invoice()
        self.assertEqual("invoiced", pos_order.state)
        self.assertEqual("posted", pos_order.account_move.state)
        self.assertTrue(pos_order.account_move.tbai_substitute_simplified_invoice)
        self.assertEqual("pending", pos_order.account_move.tbai_invoice_id.state)

    def test_open_session_error_seq(self):
        with self.assertRaises(exceptions.ValidationError):
            self.pos_config.iface_l10n_es_simplified_invoice = False
            self.pos_config.open_session_cb()

        with self.assertRaises(exceptions.ValidationError):
            self.pos_config.iface_l10n_es_simplified_invoice = True
            self.pos_config.open_session_cb()
            self.pos_config.iface_l10n_es_simplified_invoice = False
            self.pos_config.open_existing_session_cb()

        self.pos_config.iface_l10n_es_simplified_invoice = True
        self.pos_config.open_session_cb()
        self.pos_config.open_existing_session_cb()
