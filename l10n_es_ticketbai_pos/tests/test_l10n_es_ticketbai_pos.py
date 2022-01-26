# Copyright 2021 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import common
from .common import TestL10nEsTicketBAIPoSCommon


@common.at_install(False)
@common.post_install(True)
class TestL10nEsTicketBAIPoSOrder(TestL10nEsTicketBAIPoSCommon):

    def setUp(self):
        super().setUp()

    def test_create_pos_order_from_ui(self):
        self.pos_config.open_session_cb()
        pos_order = self.create_pos_order_from_ui(self.account_billing)
        self.assertEqual('paid', pos_order.state)
        self.assertEqual('pending', pos_order.tbai_invoice_id.state)

    def test_create_pos_orders_from_ui(self):
        self.pos_config.open_session_cb()
        pos_order = self.create_pos_order_from_ui(self.account_billing)
        self.assertEqual('paid', pos_order.state)
        self.assertEqual('pending', pos_order.tbai_invoice_id.state)
        pos_order2 = self.create_pos_order_from_ui2(self.account_billing)
        self.assertEqual('paid', pos_order2.state)
        self.assertEqual('pending', pos_order2.tbai_invoice_id.state)

    def test_create_invoice_from_ui(self):
        self.pos_config.open_session_cb()
        pos_order = self.create_pos_order_from_ui(
            self.account_billing, partner_id=self.partner.id,
            fp=self.fiscal_position_national, to_invoice=True)
        self.assertEqual('invoiced', pos_order.state)
        self.assertFalse(pos_order.tbai_invoice_id)
        self.assertEqual('open', pos_order.invoice_id.state)
        self.assertEqual('pending', pos_order.invoice_id.tbai_invoice_id.state)

    def test_create_invoice_from_ui_partner(self):
        self.pos_config.open_session_cb()
        pos_order = self.create_pos_order_from_ui(
            self.account_billing, partner_id=self.partner.id, to_invoice=True)
        self.assertEqual('invoiced', pos_order.state)
        self.assertFalse(pos_order.tbai_invoice_id)
        self.assertEqual('open', pos_order.invoice_id.state)
        self.assertEqual('pending', pos_order.invoice_id.tbai_invoice_id.state)

    def test_create_pos_order(self):
        self.pos_config.open_session_cb()
        pos_order = self.create_pos_order(self.account_billing.id)
        self.assertFalse(pos_order.tbai_invoice_id)
        pos_order.sudo()._tbai_build_invoice()
        pos_order.sudo()._prepare_done_order_for_pos()
        self.assertEqual('paid', pos_order.state)
        self.assertEqual('pending', pos_order.tbai_invoice_id.state)

    def test_create_invoice_from_pos_order(self):
        self.pos_config.open_session_cb()
        pos_order = self.create_pos_order(self.account_billing.id)
        self.assertFalse(pos_order.tbai_invoice_id)
        pos_order.sudo()._tbai_build_invoice()
        self.assertEqual('paid', pos_order.state)
        self.assertEqual('pending', pos_order.tbai_invoice_id.state)
        pos_order.action_pos_order_invoice()
        self.assertEqual('invoiced', pos_order.state)
        pos_order.invoice_id.sudo().with_context(
            force_company=pos_order.company_id.id,
            pos_picking_id=pos_order.picking_id
        ).action_invoice_open()
        pos_order.account_move = pos_order.invoice_id.move_id
        self.assertEqual('open', pos_order.invoice_id.state)
        self.assertEqual('pending', pos_order.invoice_id.tbai_invoice_id.state)
