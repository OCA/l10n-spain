# Copyright 2021 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields
from odoo.tests import common

from odoo.addons.l10n_es_ticketbai.tests.common import TestL10nEsTicketBAI


@common.tagged("-at_install", "post_install")
class TestL10nEsTicketBAIPoSCommon(TestL10nEsTicketBAI):
    def create_pos_order_from_ui(
        self, user, partner_id=False, fp=False, to_invoice=False
    ):
        untax, atax = 100.0, 21.0
        tax_ids = [self.tax_21b.id]
        if fp:
            vat_regime_key = fp.tbai_vat_regime_key.id
        else:
            vat_regime_key = self.env.ref("l10n_es_ticketbai.tbai_vat_regime_01").id
        orders = [
            {
                "data": {
                    "tbai_datas": "",
                    "tbai_signature_value": "",
                    "amount_return": 0.0,
                    "amount_paid": untax + atax,
                    "amount_tax": atax,
                    "amount_total": untax + atax,
                    "creation_date": str(fields.Datetime.now()),
                    "fiscal_position_id": fp and fp.id or False,
                    "pricelist_id": self.pos_config.available_pricelist_ids[0].id,
                    "tbai_vat_regime_key": vat_regime_key,
                    "lines": [
                        [
                            0,
                            0,
                            {
                                "discount": 0.0,
                                "price_unit": 100.0,
                                "product_id": self.product_delivery.id,
                                "qty": 1.0,
                                "tax_ids": [(6, 0, tax_ids)],
                                "price_subtotal": 100.0,
                                "price_subtotal_incl": 100.0,
                            },
                        ]
                    ],
                    "name": "TBAI Simplified Invoice Test - 00001-065-0016",
                    "simplified_invoice": "Shop0001",
                    "l10n_es_unique_id": "Shop0001",
                    "partner_id": partner_id,
                    "pos_session_id": self.pos_config.current_session_id.id,
                    "sequence_number": 1,
                    "statement_ids": [
                        [
                            0,
                            0,
                            {
                                "account_id": user.partner_id.property_account_receivable_id.id,
                                "amount": untax + atax,
                                "name": fields.Datetime.now(),
                                "payment_method_id": self.env.ref(
                                    "account.account_payment_method_manual_out"
                                ).id,
                                "statement_id": (
                                    self.pos_config.current_session_id.statement_ids[
                                        0
                                    ].id
                                ),
                            },
                        ]
                    ],
                    "uid": "00001-065-0016",
                    "user_id": user.id,
                    "to_invoice": to_invoice,
                },
                "to_invoice": to_invoice,
            }
        ]
        order = self.env["pos.order"].with_user(user.id).create_from_ui(orders)
        return self.env["pos.order"].browse(order[0]["id"])

    def create_pos_order_from_ui2(
        self, user, partner_id=False, fp=False, to_invoice=False
    ):
        untax, atax = 100.0, 21.0
        tax_ids = [self.tax_21b.id]
        if fp:
            vat_regime_key = fp.tbai_vat_regime_key.id
        else:
            vat_regime_key = self.env.ref("l10n_es_ticketbai.tbai_vat_regime_01").id
        orders = [
            {
                "data": {
                    "tbai_datas": "",
                    "tbai_signature_value": "",
                    "amount_return": 0.0,
                    "amount_paid": untax + atax,
                    "amount_tax": atax,
                    "amount_total": untax + atax,
                    "creation_date": str(fields.Datetime.now()),
                    "fiscal_position_id": fp and fp.id or False,
                    "pricelist_id": self.pos_config.available_pricelist_ids[0].id,
                    "tbai_vat_regime_key": vat_regime_key,
                    "lines": [
                        [
                            0,
                            0,
                            {
                                "discount": 0.0,
                                "price_unit": 100.0,
                                "product_id": self.product_delivery.id,
                                "qty": 1.0,
                                "tax_ids": [(6, 0, tax_ids)],
                                "price_subtotal": 100,
                                "price_subtotal_incl": 100,
                            },
                        ]
                    ],
                    "name": "TBAI Simplified Invoice Test - 00001-065-0017",
                    "tbai_previous_order_pos_reference": "Main0001",
                    "simplified_invoice": "Shop0002",
                    "l10n_es_unique_id": "Shop0002",
                    "partner_id": partner_id,
                    "pos_session_id": self.pos_config.current_session_id.id,
                    "sequence_number": 1,
                    "statement_ids": [
                        [
                            0,
                            0,
                            {
                                "account_id": user.partner_id.property_account_receivable_id.id,
                                "amount": untax + atax,
                                "name": fields.Datetime.now(),
                                "payment_method_id": self.env.ref(
                                    "account.account_payment_method_manual_out"
                                ).id,
                                "statement_id": (
                                    self.pos_config.current_session_id.statement_ids[
                                        0
                                    ].id
                                ),
                            },
                        ]
                    ],
                    "uid": "00001-065-0017",
                    "user_id": user.id,
                    "to_invoice": to_invoice,
                },
                "to_invoice": to_invoice,
            }
        ]
        order = self.env["pos.order"].with_user(user.id).create_from_ui(orders)
        return self.env["pos.order"].browse(order[0]["id"])

    def create_pos_order(self, uid, fp=False):
        tax_ids = [self.tax_21b.id]
        if fp:
            vat_regime_key = fp.tbai_vat_regime_key.id
        else:
            vat_regime_key = self.env.ref("l10n_es_ticketbai.tbai_vat_regime_01").id
        vals = {
            "pos_reference": "Shop0001",
            "l10n_es_unique_id": "Shop0001",
            "company_id": self.main_company.id,
            "session_id": self.pos_config.current_session_id.id,
            "partner_id": self.partner.id,
            "fiscal_position_id": fp and fp.id or False,
            "pricelist_id": self.pos_config.available_pricelist_ids[0].id,
            "tbai_vat_regime_key": vat_regime_key,
            "lines": [
                (
                    0,
                    0,
                    {
                        "name": "TBAI Simplified Invoice Line Test - delivery 1",
                        "product_id": self.product_delivery.id,
                        "price_unit": 100.0,
                        "discount": 0.0,
                        "qty": 1.0,
                        "tax_ids": [(6, 0, tax_ids)],
                        "price_subtotal": 100,
                        "price_subtotal_incl": 100,
                    },
                )
            ],
            "amount_tax": 0,
            "amount_total": 100,
            "amount_paid": 121,
            "amount_return": 0,
        }
        pos_order = self.env["pos.order"].with_user(uid).create(vals)
        payment = (
            self.env["pos.make.payment"]
            .with_context(active_ids=[pos_order.id], active_id=pos_order.id)
            .create({"amount": pos_order.amount_total})
        )
        payment.with_context(active_id=pos_order.id).check()
        return pos_order

    def setUp(self):
        super().setUp()
        self.product_delivery.available_in_pos = True
        self.pos_config = self.env.ref("point_of_sale.pos_config_main")
        self.pos_config.available_pricelist_ids.write(
            {"currency_id": self.pos_config.currency_id.id}
        )
        self.pos_config.iface_l10n_es_simplified_invoice = True
        self.account_billing.groups_id = [
            (4, self.env.ref("point_of_sale.group_pos_user").id)
        ]
