import uuid

from psycopg2 import OperationalError

from odoo import fields
from odoo.tests.common import tagged

from odoo.addons.l10n_es_aeat_verifactu.tests.test_l10n_es_aeat_verifactu import (
    TestL10nEsAeatVerifactuBase,
)


@tagged("post_install", "-at_install")
class TestL10nEsAeatVerifactuPOS(TestL10nEsAeatVerifactuBase):
    @classmethod
    def copy_account(cls, account, default=None):
        suffix_nb = 1
        while True:
            new_code = "%s.%s" % (account.code, suffix_nb)
            if account.search_count(
                [("company_id", "=", account.company_id.id), ("code", "=", new_code)]
            ):
                suffix_nb += 1
            else:
                return account.copy(default={**(default or {}), "code": new_code})

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        sequence = cls.env["ir.sequence"].create(
            {
                "name": "POS Simplified Invoice",
                "prefix": "SIM/",
                "padding": 4,
            }
        )
        sale_journal = cls.env["account.journal"].create(
            {
                "name": "PoS Sale EUR",
                "type": "sale",
                "code": "POSE",
                "company_id": cls.company.id,
                "sequence": 12,
                "currency_id": cls.env.ref("base.EUR").id,
            }
        )
        invoice_sale_journal = sale_journal.copy(
            {
                "name": "Invoice Sale EUR",
                "code": "ISE",
            }
        )
        cls.pos_config = cls.env["pos.config"].create(
            {
                "name": "Test POS",
                "company_id": cls.company.id,
                "l10n_es_simplified_invoice_limit": 3000,
                "l10n_es_simplified_invoice_sequence_id": sequence.id,
                "journal_id": sale_journal.id,
                "invoice_journal_id": invoice_sale_journal.id,
                "iface_l10n_es_simplified_invoice": True,
                "default_partner_id": cls.env["res.partner"]
                .create(
                    {
                        "name": "Test simplified default customer",
                        "aeat_simplified_invoice": True,
                    }
                )
                .id,
            }
        )
        cls.company.account_default_pos_receivable_account_id = cls.env[
            "account.account"
        ].create(
            {
                "code": "X1012.POS",
                "name": "Debtors - (POS)",
                "reconcile": True,
                "account_type": "asset_receivable",
            }
        )
        cls.pos_receivable_account = (
            cls.company.account_default_pos_receivable_account_id
        )
        cls.pos_receivable_cash = cls.copy_account(
            cls.company.account_default_pos_receivable_account_id,
            {"name": "POS Receivable Cash"},
        )
        cls.pos_receivable_bank = cls.copy_account(
            cls.company.account_default_pos_receivable_account_id,
            {"name": "POS Receivable Bank"},
        )
        cls.outstanding_bank = cls.copy_account(
            cls.company.account_journal_payment_debit_account_id,
            {"name": "Outstanding Bank"},
        )
        cls.default_journal_cash = cls.env["account.journal"].search(
            [("company_id", "=", cls.company.id), ("type", "=", "cash")], limit=1
        )
        cls.default_journal_bank = cls.env["account.journal"].search(
            [("company_id", "=", cls.company.id), ("type", "=", "bank")], limit=1
        )
        cls.cash_pm1 = cls.env["pos.payment.method"].create(
            {
                "name": "Cash",
                "journal_id": cls.default_journal_cash.id,
                "receivable_account_id": cls.pos_receivable_cash.id,
                "company_id": cls.env.company.id,
            }
        )
        cls.bank_pm1 = cls.env["pos.payment.method"].create(
            {
                "name": "Bank",
                "journal_id": cls.default_journal_bank.id,
                "receivable_account_id": cls.pos_receivable_bank.id,
                "outstanding_account_id": cls.outstanding_bank.id,
                "company_id": cls.env.company.id,
            }
        )
        cls.pos_config.write(
            {"payment_method_ids": [(6, 0, (cls.cash_pm1 + cls.bank_pm1).ids)]}
        )
        cls.pos_config.open_ui()
        cls.pos_session = cls.pos_config.current_session_id

        cls.tax_21 = cls.env.ref(
            f"l10n_es.{cls.company.id}_account_tax_template_s_iva21b"
        )
        cls.tax_10 = cls.env.ref(
            f"l10n_es.{cls.company.id}_account_tax_template_s_iva10b"
        )

    def _create_ui_order_data(self, amount=100, simplified=True):
        """Helper to create UI order data"""
        uid = str(uuid.uuid4())
        return {
            "data": {
                "amount_paid": amount * 1.21,
                "amount_total": amount * 1.21,
                "amount_tax": amount * 0.21,
                "amount_return": 0,
                "creation_date": fields.Datetime.to_string(fields.Datetime.now()),
                "fiscal_position_id": False,
                "pricelist_id": self.pos_config.available_pricelist_ids[0].id,
                "lines": [
                    [
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "price_unit": amount,
                            "qty": 1,
                            "tax_ids": [[6, False, self.tax_21.ids]],
                            "price_subtotal": amount,
                            "price_subtotal_incl": amount * 1.21,
                        },
                    ]
                ],
                "name": "Order 0001",
                "pos_session_id": self.pos_session.id,
                "sequence_number": 2,
                "partner_id": self.partner.id,
                "l10n_es_unique_id": simplified and "SIM/0001" or False,
                "uid": uid,
                "user_id": self.env.uid,
                "statement_ids": [
                    (
                        0,
                        0,
                        {
                            "amount": amount * 1.21,
                            "name": fields.Datetime.now(),
                            "payment_method_id": self.cash_pm1.id,
                        },
                    )
                ],
            },
            "id": uid,
            "to_invoice": not simplified,
        }

    def test_simplified_invoice_verifactu_flow(self):
        orders_data = [self._create_ui_order_data()]
        order_ids = self.env["pos.order"].create_from_ui(orders_data)
        order = self.env["pos.order"].browse(order_ids[0]["id"])

        self.assertTrue(
            order.is_l10n_es_simplified_invoice,
            "Order should be marked as simplified invoice",
        )
        self.assertEqual(
            order.l10n_es_unique_id,
            "SIM/0001",
            "Order should have correct simplified invoice number",
        )

        self.assertTrue(
            order.verifactu_enabled,
            "Verifactu should be enabled for simplified invoices",
        )
        self.assertEqual(
            order._get_verifactu_document_type(),
            "F2",
            "Document type should be F2 for simplified invoices",
        )
        self.assertEqual(
            order._get_document_serial_number(),
            "SIM/0001",
            "Serial number should match simplified invoice number",
        )

    def test_verifactu_hash_string(self):
        """Test the generation of Verifactu hash string for POS orders"""
        orders_data = [self._create_ui_order_data()]
        order_ids = self.env["pos.order"].create_from_ui(orders_data)
        order = self.env["pos.order"].browse(order_ids[0]["id"])

        hash_string = order._get_verifactu_hash_string()
        components = dict(item.split("=") for item in hash_string.split("&"))

        self.assertEqual(
            components["IDEmisorFactura"],
            self.company.partner_id._parse_aeat_vat_info()[2],
            "Incorrect issuer ID",
        )
        self.assertEqual(
            components["NumSerieFactura"],
            "SIM/0001",
            "Incorrect serial number",
        )
        self.assertEqual(
            components["TipoFactura"],
            "F2",
            "Incorrect document type for POS order",
        )
        self.assertEqual(
            float(components["CuotaTotal"]),
            21.0,
            "Incorrect tax amount",
        )
        self.assertEqual(
            float(components["ImporteTotal"]),
            121.0,
            "Incorrect total amount",
        )

    def test_verifactu_invoice_dict_out(self):
        """Test the generation of outgoing invoice dictionary for POS orders"""
        orders_data = [self._create_ui_order_data()]
        order_ids = self.env["pos.order"].create_from_ui(orders_data)
        order = self.env["pos.order"].browse(order_ids[0]["id"])

        result = order._get_verifactu_invoice_dict_out()
        self.assertIn("RegistroAlta", result)
        alta = result["RegistroAlta"]

        self.assertEqual(
            alta["IDFactura"]["IDEmisorFactura"],
            self.company.partner_id._parse_aeat_vat_info()[2],
        )
        self.assertEqual(alta["IDFactura"]["NumSerieFactura"], "SIM/0001")
        self.assertEqual(alta["TipoFactura"], "F2")
        self.assertEqual(float(alta["CuotaTotal"]), 21.0)
        self.assertEqual(float(alta["ImporteTotal"]), 121.0)

    def test_verifactu_chaining_first_order(self):
        """Test chaining when there's no previous POS order"""
        self.pos_config.verifactu_last_invoice_id = False
        orders_data = [self._create_ui_order_data()]
        order_ids = self.env["pos.order"].create_from_ui(orders_data)
        order = self.env["pos.order"].browse(order_ids[0]["id"])

        result = order._get_chaining_invoice_dict()
        self.assertEqual(
            result,
            {"PrimerRegistro": "S"},
            "Should indicate first record when no previous order exists",
        )
        self.assertEqual(
            self.pos_config.verifactu_last_invoice_id.id,
            order.id,
            "Config's last order should be updated for first record",
        )

    def test_verifactu_chaining_with_previous(self):
        """Test chaining when there's a previous POS order"""
        orders_data = [self._create_ui_order_data()]
        first_order_ids = self.env["pos.order"].create_from_ui(orders_data)
        first_order = self.env["pos.order"].browse(first_order_ids[0]["id"])
        first_order.verifactu_hash = "TEST_HASH"
        self.pos_config.verifactu_last_invoice_id = first_order.id

        second_order_data = self._create_ui_order_data(amount=200)
        second_order_data["data"]["name"] = "Order 0002"
        second_order_data["data"]["uid"] = str(uuid.uuid4())  # New unique ID
        second_order_data["id"] = second_order_data["data"]["uid"]
        second_order_ids = self.env["pos.order"].create_from_ui([second_order_data])
        second_order = self.env["pos.order"].browse(second_order_ids[0]["id"])

        result = second_order._get_chaining_invoice_dict()
        self.assertIn("RegistroAnterior", result)
        self.assertEqual(
            result["RegistroAnterior"]["NumSerieFactura"],
            "SIM/0001",
            "Should contain previous order reference",
        )
        self.assertEqual(
            result["RegistroAnterior"]["Huella"],
            "TEST_HASH",
            "Should contain previous order hash",
        )
        self.assertEqual(
            self.pos_config.verifactu_last_invoice_id.id,
            second_order.id,
            "Should update config's last order reference",
        )

    def test_verifactu_chaining_operational_error(self):
        """Test handling of OperationalError during chaining"""

        def mock_execute(*args, **kwargs):
            raise OperationalError("Test lock error")

        orders_data = [self._create_ui_order_data()]
        first_order_ids = self.env["pos.order"].create_from_ui(orders_data)
        first_order = self.env["pos.order"].browse(first_order_ids[0]["id"])
        self.pos_config.verifactu_last_invoice_id = first_order.id

        second_order_data = self._create_ui_order_data(amount=200)
        second_order_data["data"]["name"] = "Order 0002"
        second_order_data["data"]["uid"] = str(uuid.uuid4())  # New unique ID
        second_order_data["id"] = second_order_data["data"]["uid"]
        second_order_ids = self.env["pos.order"].create_from_ui([second_order_data])
        second_order = self.env["pos.order"].browse(second_order_ids[0]["id"])

        old_execute = self.cr.execute
        with self.assertRaises(OperationalError):
            with self.cr.savepoint():
                self.cr.execute = mock_execute
                second_order._get_chaining_invoice_dict()
        self.cr.execute = old_execute

        self.assertEqual(
            self.pos_config.verifactu_last_invoice_id.id,
            first_order.id,
            "Should not update config's last order reference on error",
        )

    def test_verifactu_chaining_invoiced_pos_order(self):
        """Test that invoiced POS orders are added to POS config chain"""
        orders_data = [self._create_ui_order_data()]
        first_order_ids = self.env["pos.order"].create_from_ui(orders_data)
        first_order = self.env["pos.order"].browse(first_order_ids[0]["id"])
        first_order.verifactu_hash = "FIRST_HASH"
        self.pos_config.verifactu_last_invoice_id = first_order.id

        second_order_data = self._create_ui_order_data(amount=200, simplified=False)
        second_order_data["data"]["name"] = "Order 0002"
        second_order_data["data"]["uid"] = str(uuid.uuid4())
        second_order_data["id"] = second_order_data["data"]["uid"]
        second_order_ids = self.env["pos.order"].create_from_ui([second_order_data])
        second_order = self.env["pos.order"].browse(second_order_ids[0]["id"])

        second_order.company_id.verifactu_last_invoice_id = False

        second_order.action_pos_order_invoice()
        invoice = second_order.account_move

        result = invoice._get_chaining_invoice_dict()
        self.assertIn(
            "RegistroAnterior", result, "Invoice should have previous record info"
        )
        self.assertEqual(
            result["RegistroAnterior"]["Huella"],
            "FIRST_HASH",
            "Invoice should link to previous POS order hash",
        )
        self.assertEqual(
            self.pos_config.verifactu_last_invoice_id.id,
            second_order.id,
            "Config's last order should be the POS order, not the invoice",
        )
        self.assertFalse(invoice.company_id.verifactu_last_invoice_id.exists())
