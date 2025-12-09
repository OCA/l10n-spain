# Copyright 2023 Aures Tic - Almudena de la Puente <almudena@aurestic.es>
# Copyright 2023 Aures Tic - Jose Zambudio <jose@aurestic.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import json

from odoo import Command
from odoo.tests import tagged
from odoo.tools.misc import file_path

from odoo.addons.l10n_es_aeat_sii_oca.tests.test_l10n_es_aeat_sii import (
    TestL10nEsAeatSiiBase,
)
from odoo.addons.point_of_sale.tests.common import TestPoSCommon


@tagged("post_install", "-at_install")
class TestSpainPosSii(TestPoSCommon, TestL10nEsAeatSiiBase):
    # Because we are using the TestPosCommon the final user is
    # 'Because I am accountman!' so we need to add the account_payment
    # group to create res.partner.bank records if account_payment_order
    # is installed
    @classmethod
    def get_default_groups(cls):
        groups = super().get_default_groups()
        group_account_payment = cls.env.ref(
            "account_payment_order.group_account_payment", raise_if_not_found=False
        )
        if group_account_payment:
            return groups | group_account_payment
        return groups

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company.write(
            {
                "sii_enabled": True,
                "sii_test": True,
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
        cls.fr_country = cls.env.ref("base.fr")
        cls.other_customer.write(
            {
                "country_id": cls.fr_country.id,
                "vat": "FR82542065479",
            }
        )
        cls.PosSession = cls.env["pos.session"]
        cls.config = cls.basic_config
        cls.config.write(
            {
                "iface_l10n_es_simplified_invoice": True,
                "company_id": cls.company.id,
            }
        )
        cls.env.user.write(
            {"groups_id": [(3, cls.env.ref("account.group_account_manager").id)]}
        )
        cls.tax_21b = cls.env.ref(
            f"account.{cls.env.user.company_id.id}_account_tax_template_s_iva21b"
        )
        cls.tax_account = cls.env.ref(
            f"account.{cls.env.user.company_id.id}_account_common_477"
        )
        cls.tax_10b = cls.env.ref(
            f"account.{cls.env.user.company_id.id}_account_tax_template_s_iva10b"
        )
        cls.product21 = cls.create_product(
            "Product 21b",
            cls.categ_basic,
            100.0,
            100.0,
            tax_ids=cls.tax_21b.ids,
        )
        cls.product10 = cls.create_product(
            "Product 10b",
            cls.categ_basic,
            100.0,
            100.0,
            tax_ids=cls.tax_10b.ids,
        )

    def setUp(self):
        super().setUp()
        self._create_session_closed()
        self.session = self.PosSession.search([], limit=1, order="id desc")
        self.order = self.session.order_ids[:1]

    @classmethod
    def _create_invoice(cls, move_type):
        return cls.env["account.move"].create(
            {
                "company_id": cls.company.id,
                "partner_id": cls.partner.id,
                "invoice_date": "2018-02-01",
                "move_type": move_type,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": cls.product.id,
                            "account_id": cls.account_expense.id,
                            "name": "Test line",
                            "price_unit": 100,
                            "quantity": 1,
                        },
                    )
                ],
            }
        )

    def _create_session_closed(self):
        cash = self.cash_pm1
        self._run_test(
            {
                "payment_methods": cash,
                "orders": [
                    {
                        "pos_order_lines_ui_args": [(self.product21, 1)],
                        "payments": [(cash, 121)],
                        "customer": False,
                        "is_invoiced": False,
                        "uuid": "00100-010-0001",
                    },
                    {
                        "pos_order_lines_ui_args": [(self.product10, 1)],
                        "payments": [(cash, 110)],
                        "customer": self.other_customer,
                        "is_invoiced": False,
                        "uuid": "00100-010-0002",
                    },
                    {
                        "pos_order_lines_ui_args": [
                            (self.product21, 1),
                            (self.product10, 1),
                        ],
                        "payments": [(cash, 231)],
                        "customer": self.customer,
                        "is_invoiced": False,
                        "uuid": "00100-010-0003",
                    },
                ],
                "journal_entries_before_closing": {},
                "journal_entries_after_closing": {
                    "session_journal_entry": {
                        "line_ids": [
                            {
                                "account_id": self.tax_account.id,
                                "partner_id": False,
                                "debit": 0,
                                "credit": 42,
                                "reconciled": False,
                            },
                            {
                                "account_id": self.tax_account.id,
                                "partner_id": False,
                                "debit": 0,
                                "credit": 20,
                                "reconciled": False,
                            },
                            {
                                "account_id": self.sales_account.id,
                                "partner_id": False,
                                "debit": 0,
                                "credit": 200,
                                "reconciled": False,
                            },
                            {
                                "account_id": self.sales_account.id,
                                "partner_id": False,
                                "debit": 0,
                                "credit": 200,
                                "reconciled": False,
                            },
                            {
                                "account_id": cash.receivable_account_id.id,
                                "partner_id": False,
                                "debit": 462,
                                "credit": 0,
                                "reconciled": True,
                            },
                        ],
                    },
                    "cash_statement": [
                        (
                            (462,),
                            {
                                "line_ids": [
                                    {
                                        "account_id": (
                                            cash.journal_id.default_account_id.id
                                        ),
                                        "partner_id": False,
                                        "debit": 462,
                                        "credit": 0,
                                        "reconciled": False,
                                    },
                                    {
                                        "account_id": cash.receivable_account_id.id,
                                        "partner_id": False,
                                        "debit": 0,
                                        "credit": 462,
                                        "reconciled": True,
                                    },
                                ]
                            },
                        )
                    ],
                    "bank_payments": [],
                },
            }
        )

    def _compare_sii_dict(self, json_file, order):
        """Helper method for comparing the expected SII dict with ."""
        module = "l10n_es_pos_sii"
        result_dict = order._get_aeat_invoice_dict()
        path = file_path(f"{module}/tests/json/{json_file}")
        if not path:
            raise Exception(f"Incorrect JSON file: {json_file}")
        with open(path) as f:
            expected_dict = json.loads(f.read())
        self.assertEqual(expected_dict, result_dict)
        return order

    def test_01_partner_sii_enabled(self):
        company_02 = self.env["res.company"].create({"name": "Company 02"})
        self.env.user.company_ids += company_02
        self.assertTrue(self.partner.sii_enabled)
        self.partner.company_id = company_02
        self.assertFalse(self.partner.sii_enabled)

    def test_02_json_orders(self):
        json_by_taxes = {
            self.tax_21b: {
                "json": "sii_pos_order_iva21b.json",
                "name": "Shop0001",
            },
            self.tax_10b: {
                "json": "sii_pos_order_iva10b.json",
                "name": "Shop0002",
            },
            (self.tax_10b + self.tax_21b): {
                "json": "sii_pos_order_iva21b_iva10b.json",
                "name": "Shop0003",
            },
        }
        for order in self.session.order_ids:
            taxes = order.lines.mapped("tax_ids_after_fiscal_position").sorted(
                key=lambda tax: tax.amount
            )
            order.write(
                {
                    "l10n_es_unique_id": json_by_taxes.get(taxes, {}).get("name"),
                    "date_order": "2023-06-14",
                }
            )
            order.send_sii()
            self._compare_sii_dict(json_by_taxes.get(taxes, {}).get("json"), order)

    def test_03_is_aeat_simplified_invoice(self):
        for order in self.session.order_ids:
            self.assertTrue(order._is_aeat_simplified_invoice())

    def test_04_sii_description(self):
        self.order.company_id.write(
            {
                "sii_pos_description": "Test POS description",
            }
        )
        session = self.order.session_id
        default_partner = self.env.ref("l10n_es.partner_simplified")
        order = self.env["pos.order"].create(
            {
                "company_id": self.order.company_id.id,
                "session_id": session.id,
                "pricelist_id": default_partner.property_product_pricelist.id,
                "partner_id": default_partner.id,
                "lines": [
                    Command.create(
                        {
                            "name": "TPV/0001",
                            "product_id": self.product21.id,
                            "price_unit": 100,
                            "discount": 0.0,
                            "qty": 1.0,
                            "tax_ids": [(6, 0, self.product21.taxes_id.ids)],
                            "price_subtotal": 100,
                            "price_subtotal_incl": 100 + 21,
                        },
                    )
                ],
                "amount_tax": 21,
                "amount_total": 100 + 21,
                "amount_paid": 121,
                "amount_return": 0,
            }
        )
        order.action_pos_order_paid()
        self.assertEqual(order.sii_description, "Test POS description")

    def test_05_refund_sii_refund_type(self):
        cash = self.cash_pm1
        self._start_pos_session(cash, 462.0)
        refund_order = self._create_orders(
            [
                {
                    "pos_order_lines_ui_args": [(self.product21, -1)],
                    "payments": [(cash, -121)],
                    "customer": False,
                    "is_invoiced": False,
                    "uuid": "00100-010-0004",
                },
            ]
        ).get("00100-010-0004")
        refund_order.write(
            {
                "l10n_es_unique_id": "Shop0004",
                "date_order": "2023-06-14",
            }
        )
        self._compare_sii_dict("sii_pos_order_refund_iva21b.json", refund_order)
        self.assertEqual(refund_order.sii_refund_type, "I")

    def test_06_automatic_send(self):
        self.company.send_mode = "auto"

        cash = self.cash_pm1
        pos_session = self._start_pos_session(cash, 462.0)

        self._create_orders(
            [
                {
                    "pos_order_lines_ui_args": [(self.product21, 1)],
                    "payments": [(cash, 121)],
                    "customer": False,
                    "is_invoiced": False,
                    "uuid": "00100-010-0004",
                },
            ]
        )

        pos_session.post_closing_cash_details(583.0)
        sii_send_cron = self.env.ref("l10n_es_aeat_sii_oca.invoice_send_to_sii")
        Trigger = self.env["ir.cron.trigger"].sudo()
        before = Trigger.search_count([("cron_id", "=", sii_send_cron.id)])

        pos_session.close_session_from_ui()

        after = Trigger.search_count([("cron_id", "=", sii_send_cron.id)])
        self.assertEqual(after, before + 1)

        trigger = Trigger.search(
            [("cron_id", "=", sii_send_cron.id)], order="id desc", limit=1
        )
        self.assertTrue(trigger)
        self.assertTrue(trigger.call_at)

    def test_07_export_for_ui_session_is_closed(self):
        cash = self.cash_pm1
        pos_session = self._start_pos_session(cash, 462.0)
        self._create_orders(
            [
                {
                    "pos_order_lines_ui_args": [(self.product21, 1)],
                    "payments": [(cash, 121)],
                    "customer": False,
                    "is_invoiced": False,
                    "uuid": "00100-010-0004",
                },
            ]
        )
        res = pos_session.order_ids.read(["sii_session_closed"])
        self.assertTrue(
            all(
                "sii_session_closed" in x and x["sii_session_closed"] is False
                for x in res
            ),
            "The session is not closed",
        )
        pos_session.post_closing_cash_details(583.0)
        pos_session.close_session_from_ui()
        res = pos_session.order_ids.read(["sii_session_closed"])
        self.assertTrue(
            all(
                "sii_session_closed" in x and x["sii_session_closed"] is True
                for x in res
            ),
            "The session is closed",
        )
