from odoo.tests import tagged

from odoo.addons.l10n_es_aeat_sii_oca.tests.test_l10n_es_aeat_sii import (
    TestL10nEsAeatSiiBase,
)
from odoo.addons.point_of_sale.tests.common import TestPoSCommon


@tagged("post_install", "-at_install")
class TestSpainPosSii(TestPoSCommon, TestL10nEsAeatSiiBase):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        chart_template_ref = (
            "l10n_es.account_chart_template_common" or chart_template_ref
        )
        super().setUpClass(chart_template_ref=chart_template_ref)
        # !: AccountTestInvoicingCommon overwrite user.company_id with sii disabled
        cls.company = cls.env.user.company_id

        # Create a new cash payment method
        cls.company.write(
            {
                "sii_enabled": True,
                "sii_test": True,
                "use_connector": True,
                "sii_method": "manual",
                "vat": "ESU2687761C",
                "sii_description_method": "manual",
                "tax_agency_id": cls.env.ref("l10n_es_aeat.aeat_tax_agency_spain"),
            }
        )
        cls.customer.write(
            {
                "country_id": cls.env.ref("base.es").id,
                "vat": "F35999705",
            }
        )
        cls.es_country = cls.env.ref("base.es")
        cls.other_customer.write(
            {
                "country_id": cls.es_country.id,
                "vat": "ESF35999705",
            }
        )

    def setUp(self):
        super(TestSpainPosSii, self).setUp()
        self.PosSession = self.env["pos.session"]
        self.PosOrder = self.env["pos.order"]
        self.PosMakePayment = self.env["pos.make.payment"]
        self.pos_product = self.env.ref("point_of_sale.whiteboard_pen")
        self.pricelist = self.env.ref("product.list0")
        self.pos_config = self.basic_config
        self.pos_config.write(
            {
                "iface_l10n_es_simplified_invoice": True,
                "company_id": self.company.id,
                "default_partner_id": self.env["res.partner"]
                .create(
                    {
                        "name": "Test simplified default customer",
                        "sii_simplified_invoice": True,
                    }
                )
                .id,
            }
        )

        self.env.user.write(
            {"groups_id": [(3, self.env.ref("account.group_account_manager").id)]}
        )
        self.tax_21b = self.env.ref(
            f"l10n_es.{self.env.user.company_id.id}_account_tax_template_s_iva21b"
        )
        self.tax_account = self.env.ref(
            f"l10n_es.{self.env.user.company_id.id}_account_common_477"
        )
        self.tax_10b = self.env.ref(
            f"l10n_es.{self.env.user.company_id.id}_account_tax_template_s_iva10b"
        )
        self.product21 = self.create_product(
            "Product 21b",
            self.categ_basic,
            100.0,
            100.0,
            tax_ids=self.tax_21b.ids,
        )
        self.product10 = self.create_product(
            "Product 10b",
            self.categ_basic,
            100.0,
            100.0,
            tax_ids=self.tax_10b.ids,
        )

        self.sales_account = self.product21.categ_id.property_account_income_categ_id
        self.cash_pm1 = self.pos_config.payment_method_ids[0]

        # Create a new pos config and open it
        self._create_session_closed()
        self.session = self.PosSession.search([], limit=1, order="id desc")
        self.order = self.session.order_ids[:1]

    def _create_session_closed(self):
        cash = self.cash_pm1
        self.pos_session = self.env["pos.session"].create(
            {"config_id": self.pos_config.id}
        )
        self.pos_session.action_pos_session_open()

        self.pos_session.update(
            {
                "payment_method_ids": cash,
                "order_ids": [
                    (
                        0,
                        0,
                        {
                            "lines": [(self.product21.id, 1)],
                            "payment_ids": [(cash.id, 121)],
                            "partner_id": False,
                            "is_invoiced": False,
                            "amount_tax": 0,
                            "fiscal_position_id": False,
                            "amount_return": 0,
                            "sequence_number": 1,
                            "amount_total": 18.0,
                            "amount_paid": 18.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "lines": [(self.product10.id, 1)],
                            "payment_ids": [(cash.id, 110)],
                            "partner_id": self.other_customer.id,
                            "is_invoiced": False,
                            "amount_tax": 0,
                            "fiscal_position_id": False,
                            "amount_return": 0,
                            "sequence_number": 1,
                            "amount_total": 18.0,
                            "amount_paid": 18.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "lines": [
                                (self.product21.id, 1),
                                (self.product10.id, 1),
                            ],
                            "payment_ids": [(cash.id, 231)],
                            "partner_id": self.customer.id,
                            "is_invoiced": False,
                            "amount_tax": 0,
                            "fiscal_position_id": False,
                            "amount_return": 0,
                            "sequence_number": 1,
                            "amount_total": 18.0,
                            "amount_paid": 18.0,
                        },
                    ),
                ],
            }
        )

        # I make a payment to fully pay the order
        for order in self.pos_session.order_ids:
            context_make_payment = {"active_ids": [order.id], "active_id": order.id}
            self.pos_make_payment_0 = self.PosMakePayment.with_context(
                context_make_payment
            ).create(
                {
                    "amount": order.amount_total,
                    "payment_method_id": self.pos_session.payment_method_ids.id,
                }
            )
            # I click on the validate button to register the payment.
            context_payment = {"active_id": order.id}
            self.pos_make_payment_0.with_context(context_payment).check()
        self.pos_session._check_pos_session_balance()
        self.pos_session.action_pos_session_close()

    def test_01_partner_sii_enabled(self):
        company_02 = self.env["res.company"].create({"name": "Company 02"})
        self.env.user.company_ids += company_02
        self.assertTrue(self.partner.sii_enabled)
        self.partner.company_id = company_02
        self.assertFalse(self.partner.sii_enabled)

    # def test_02_json_orders(self):
    #     json_by_taxes = {
    #         self.tax_21b: {
    #             "json": "sii_pos_order_iva21b.json",
    #             "name": "Shop0001",
    #         },
    #         self.tax_10b: {
    #             "json": "sii_pos_order_iva10b.json",
    #             "name": "Shop0002",
    #         },
    #         (self.tax_10b + self.tax_21b): {
    #             "json": "sii_pos_order_iva21b_iva10b.json",
    #             "name": "Shop0003",
    #         },
    #     }
    #     for order in self.session.order_ids:
    #         taxes = order.lines.mapped("tax_ids_after_fiscal_position").sorted(
    #             key=lambda tax: tax.amount
    #         )
    #         order.write(
    #             {
    #                 "l10n_es_unique_id": json_by_taxes.get(taxes, {}).get(
    #                     "name"),
    #                 "date_order": "2023-06-14",
    #             }
    #         )
    #         order.send_sii()
    #         self._compare_sii_dict(json_by_taxes.get(taxes, {}).get("json"),
    #                                order)

    def test_03_job_creation(self):
        for order in self.session.order_ids:
            order.send_sii()
            self.assertTrue(order.order_jobs_ids)

    def test_04_is_sii_simplified_invoice(self):
        for order in self.session.order_ids:
            self.assertTrue(order._is_sii_simplified_invoice())

    def test_05_sii_description(self):
        company = self.order.company_id
        self.assertEqual(self.order.sii_description, "/")
        company.write(
            {
                "sii_pos_description": "Test POS description",
            }
        )
        self.order._compute_sii_description()
        self.assertEqual(self.order.sii_description, "Test POS description")

    # def test_06_refund_sii_refund_type(self):
    #     cash = self.cash_pm1
    #     self._start_pos_session(cash, 462.0)
    #     refund_order = self._create_orders(
    #         [
    #             {
    #                 "pos_order_lines_ui_args": [(self.product21, -1)],
    #                 "payments": [(cash, -121)],
    #                 "customer": False,
    #                 "is_invoiced": False,
    #                 "uid": "00100-010-0004",
    #             },
    #         ]
    #     ).get("00100-010-0004")
    #     refund_order.write(
    #         {
    #             "l10n_es_unique_id": "Shop0004",
    #             "date_order": "2023-06-14",
    #         }
    #     )
    #     self._compare_sii_dict("sii_pos_order_refund_iva21b.json", refund_order)
    #
    # def test_07_automatic_send(self):
    #     self.company.sii_description_method = "auto"
    #     cash = self.cash_pm1
    #     pos_session = self._start_pos_session(cash, 462.0)
    #     self._create_orders(
    #         [
    #             {
    #                 "pos_order_lines_ui_args": [(self.product21, 1)],
    #                 "payments": [(cash, 121)],
    #                 "customer": False,
    #                 "is_invoiced": False,
    #                 "uid": "00100-010-0004",
    #             },
    #         ]
    #     )
    #     pos_session.post_closing_cash_details(583.0)
    #     pos_session.close_session_from_ui()
    #     for order in pos_session.order_ids:
    #         self.assertTrue(order.order_jobs_ids)
