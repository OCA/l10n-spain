import uuid

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import tagged

from odoo.addons.l10n_es_verifactu_oca.tests.common import TestVerifactuCommon


@tagged("post_install", "-at_install")
class TestL10nEsVerifactuPOS(TestVerifactuCommon):
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
        # Enable verifactu for deterministic testing
        self.company.verifactu_enabled = True
        self.pos_config.journal_id.verifactu_enabled = True

        orders_data = [self._create_ui_order_data()]
        order_ids = self.env["pos.order"].create_from_ui(orders_data)
        order = self.env["pos.order"].browse(order_ids[0]["id"])

        # Ensure order is in the correct state for verifactu processing
        order.state = "paid"
        order._compute_verifactu_enabled()

        # Now the hash string should be generated deterministically
        hash_string = order._get_verifactu_hash_string()
        self.assertTrue(
            hash_string, "Hash string should be generated when verifactu is enabled"
        )

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
        """Test new chaining system works correctly"""
        orders_data = [self._create_ui_order_data()]
        order_ids = self.env["pos.order"].create_from_ui(orders_data)
        order = self.env["pos.order"].browse(order_ids[0]["id"])

        # Check that the order uses company-wide chaining
        chaining = order._get_verifactu_chaining()
        self.assertEqual(
            chaining,
            self.company.verifactu_chaining_id,
            "Should use company-wide chaining",
        )

        # Check chaining dict generation
        result = order._get_verifactu_chaining_invoice_dict()
        if not order.last_verifactu_invoice_entry_id:
            self.assertEqual(
                result,
                {"PrimerRegistro": "S"},
                "Should indicate first record when no previous entry exists",
            )
        else:
            # If there's a previous entry, check the structure
            if order.last_verifactu_invoice_entry_id.previous_invoice_entry_id:
                self.assertIn("RegistroAnterior", result)
            else:
                self.assertEqual(result, {"PrimerRegistro": "S"})

    def test_pos_verifactu_multi_order_chaining(self):
        """Test that multiple POS orders are properly chained together"""
        # Create first POS order
        orders_data_1 = [self._create_ui_order_data(amount=100)]
        order_ids_1 = self.env["pos.order"].create_from_ui(orders_data_1)
        order_1 = self.env["pos.order"].browse(order_ids_1[0]["id"])

        # Create second POS order
        orders_data_2 = [self._create_ui_order_data(amount=200)]
        order_ids_2 = self.env["pos.order"].create_from_ui(orders_data_2)
        order_2 = self.env["pos.order"].browse(order_ids_2[0]["id"])

        # Verify first order has no previous hash
        self.assertFalse(
            order_1._get_verifactu_previous_hash(),
            "First order should have no previous hash",
        )

        # Verify second order references first order's hash
        first_hash = order_1.verifactu_hash
        second_previous_hash = order_2._get_verifactu_previous_hash()
        self.assertEqual(
            second_previous_hash,
            first_hash,
            "Second order should reference first order's hash",
        )

        # Verify hash strings include previous hashes
        first_hash_string = order_1._get_verifactu_hash_string()
        second_hash_string = order_2._get_verifactu_hash_string()

        # First order should have empty hash value (Huella=&)
        self.assertIn(
            "Huella=&",
            first_hash_string,
            "First order hash string should include empty previous hash parameter",
        )
        self.assertIn(
            f"Huella={first_hash}",
            second_hash_string,
            "Second order hash string should include first order's hash",
        )

    def test_pos_verifactu_disabled_company(self):
        """Test POS order when VeriFactu is disabled for company"""
        # Disable VeriFactu for company
        self.company.verifactu_enabled = False

        orders_data = [self._create_ui_order_data()]
        order_ids = self.env["pos.order"].create_from_ui(orders_data)
        order = self.env["pos.order"].browse(order_ids[0]["id"])

        # Should not be enabled for VeriFactu
        self.assertFalse(
            order.verifactu_enabled,
            "Order should not be VeriFactu enabled when company disabled",
        )

        # Hash string should be empty
        self.assertEqual(
            order._get_verifactu_hash_string(),
            "",
            "Hash string should be empty when VeriFactu disabled",
        )

    def test_pos_verifactu_refund_detection(self):
        """Test that POS refunds are properly detected"""
        # Create a refund order (negative amount)
        orders_data = [self._create_ui_order_data(amount=-100)]
        order_ids = self.env["pos.order"].create_from_ui(orders_data)
        order = self.env["pos.order"].browse(order_ids[0]["id"])

        # Should be detected as refund
        self.assertTrue(
            order._is_refund_order(), "Should detect negative amount as refund"
        )
        self.assertEqual(
            order._get_verifactu_document_type(), "R5", "Should use R5 for refunds"
        )
        self.assertEqual(
            order.verifactu_refund_type, "I", "Should set refund type to 'I'"
        )

    def test_pos_verifactu_refund_rectification(self):
        """Test that refunds include proper rectification references"""
        # Create original order
        orders_data_1 = [self._create_ui_order_data(amount=100)]
        order_ids_1 = self.env["pos.order"].create_from_ui(orders_data_1)
        order_1 = self.env["pos.order"].browse(order_ids_1[0]["id"])

        # Create refund order
        orders_data_2 = [self._create_ui_order_data(amount=-50)]
        order_ids_2 = self.env["pos.order"].create_from_ui(orders_data_2)
        order_2 = self.env["pos.order"].browse(order_ids_2[0]["id"])

        # Set up refund relationship (simulate POS refund linking)
        order_2.refunded_order_ids = order_1

        # Check rectification in invoice dict
        result = order_2._get_verifactu_invoice_dict_out()
        alta = result["RegistroAlta"]

        self.assertIn("TipoRectificativa", alta, "Should include rectification type")
        self.assertEqual(alta["TipoRectificativa"], "I", "Should be 'I' rectification")
        self.assertIn("FacturasRectificadas", alta, "Should include rectified invoices")

        # Check that it references the original order
        rectified_invoice = alta["FacturasRectificadas"][0]["IDFacturaRectificada"]
        self.assertEqual(
            rectified_invoice["NumSerieFactura"], order_1._get_document_serial_number()
        )

    def test_pos_verifactu_l10n_es_pos_integration(self):
        """Test integration with l10n_es_pos simplified invoices"""
        # Test that simplified invoice numbers are used correctly
        orders_data = [self._create_ui_order_data(amount=100, simplified=True)]
        order_ids = self.env["pos.order"].create_from_ui(orders_data)
        order = self.env["pos.order"].browse(order_ids[0]["id"])

        # Should use simplified invoice number as serial
        self.assertTrue(
            order.l10n_es_unique_id, "Should have simplified invoice number"
        )
        self.assertEqual(order._get_document_serial_number(), order.l10n_es_unique_id)

        # Should be marked as simplified invoice
        self.assertTrue(order.is_l10n_es_simplified_invoice)

        # Should use F2 document type for positive amounts
        self.assertEqual(order._get_verifactu_document_type(), "F2")

    def test_pos_verifactu_refund_hash_generation(self):
        """Test that refund orders generate proper hash strings"""
        # Create a refund order
        orders_data = [self._create_ui_order_data(amount=-100)]
        order_ids = self.env["pos.order"].create_from_ui(orders_data)
        order = self.env["pos.order"].browse(order_ids[0]["id"])

        # Generate hash string
        hash_string = order._get_verifactu_hash_string()

        # Should include refund document type
        self.assertIn(
            "TipoFactura=R5", hash_string, "Should use R5 document type in hash"
        )

        self.assertIn("CuotaTotal=-21", hash_string, "Should be negative tax amount")
        self.assertIn(
            "ImporteTotal=-121", hash_string, "Should be negative total amount"
        )

    def test_pos_verifactu_mixed_order_types(self):
        """Test handling of both sales and refunds in sequence"""
        # Create a sale order
        orders_data_sale = [self._create_ui_order_data(amount=100)]
        order_ids_sale = self.env["pos.order"].create_from_ui(orders_data_sale)
        order_sale = self.env["pos.order"].browse(order_ids_sale[0]["id"])

        # Create a refund order
        orders_data_refund = [self._create_ui_order_data(amount=-50)]
        order_ids_refund = self.env["pos.order"].create_from_ui(orders_data_refund)
        order_refund = self.env["pos.order"].browse(order_ids_refund[0]["id"])

        # Verify different document types
        self.assertEqual(
            order_sale._get_verifactu_document_type(), "F2", "Sale should be F2"
        )
        self.assertEqual(
            order_refund._get_verifactu_document_type(), "R5", "Refund should be R5"
        )

        # Verify different refund types
        self.assertFalse(
            order_sale.verifactu_refund_type, "Sale should have no refund type"
        )
        self.assertEqual(
            order_refund.verifactu_refund_type, "I", "Refund should have 'I' type"
        )

        # Verify amount handling
        _tx_dict, _am_tax, amount_total = order_sale._get_verifactu_taxes_and_total()
        self.assertEqual(amount_total, 121.0)
        _tx_dict, _am_tax, amount_total = order_refund._get_verifactu_taxes_and_total()
        self.assertEqual(amount_total, -60.5)

    def test_pos_verifactu_start_date(self):
        """Test POS order verifactu enablement with start date"""
        # Set start date to 2018-01-01
        self.company.verifactu_start_date = "2018-01-01"

        # Create order after start date (should be enabled)
        orders_data_after = [self._create_ui_order_data()]
        orders_data_after[0]["data"]["name"] = "Order AFTER 001"
        orders_data_after[0]["data"]["uid"] = str(uuid.uuid4())
        order_ids_after = self.env["pos.order"].create_from_ui(orders_data_after)
        order_after = self.env["pos.order"].browse(order_ids_after[0]["id"])

        # Force date to be after start date
        order_after.date_order = fields.Datetime.from_string("2019-01-01 10:00:00")
        order_after._compute_verifactu_enabled()
        self.assertTrue(
            order_after.verifactu_enabled,
            "POS order should be verifactu enabled when date is after start date",
        )

        # Create order before start date (should be disabled)
        orders_data_before = [self._create_ui_order_data()]
        orders_data_before[0]["data"]["name"] = "Order BEFORE 001"
        orders_data_before[0]["data"]["uid"] = str(uuid.uuid4())
        order_ids_before = self.env["pos.order"].create_from_ui(orders_data_before)
        order_before = self.env["pos.order"].browse(order_ids_before[0]["id"])

        # Force date to be before start date
        order_before.date_order = fields.Datetime.from_string("2017-01-01 10:00:00")
        order_before._compute_verifactu_enabled()
        self.assertFalse(
            order_before.verifactu_enabled,
            "POS order should not be verifactu enabled when date is before start date",
        )

        # Disable start date - order before should now be enabled
        self.company.verifactu_start_date = False
        order_before._compute_verifactu_enabled()
        self.assertTrue(
            order_before.verifactu_enabled,
            "POS order should be verifactu enabled when start date is disabled",
        )

    def test_pos_verifactu_registration_key_computation(self):
        """Test that POS orders compute verifactu registration keys correctly"""
        # Create order with fiscal position
        orders_data = [self._create_ui_order_data()]
        orders_data[0]["data"]["fiscal_position_id"] = self.fp_nacional.id
        order_ids = self.env["pos.order"].create_from_ui(orders_data)
        order = self.env["pos.order"].browse(order_ids[0]["id"])

        # Should use fiscal position's registration key
        self.assertEqual(
            order.verifactu_registration_key,
            self.fp_registration_key_01,
            "Should use fiscal position's registration key",
        )
        self.assertEqual(
            order.verifactu_registration_key_code,
            "01",
            "Should compute registration key code correctly",
        )

    def test_pos_verifactu_tax_key_computation(self):
        """Test that POS orders compute verifactu tax keys correctly"""
        # Create order with fiscal position
        orders_data = [self._create_ui_order_data()]
        orders_data[0]["data"]["fiscal_position_id"] = self.fp_nacional.id
        order_ids = self.env["pos.order"].create_from_ui(orders_data)
        order = self.env["pos.order"].browse(order_ids[0]["id"])

        # Should compute tax key from fiscal position or default to "01"
        expected_tax_key = self.fp_nacional.verifactu_tax_key or "01"
        self.assertEqual(
            order.verifactu_tax_key,
            expected_tax_key,
            "Should compute tax key from fiscal position or default to '01'",
        )

    def test_pos_verifactu_registration_key_without_fiscal_position(self):
        """Test registration key computation when no fiscal position is set"""
        # Create order without fiscal position
        orders_data = [self._create_ui_order_data()]
        orders_data[0]["data"]["fiscal_position_id"] = False
        order_ids = self.env["pos.order"].create_from_ui(orders_data)
        order = self.env["pos.order"].browse(order_ids[0]["id"])

        # Should find default registration key
        self.assertTrue(
            order.verifactu_registration_key,
            "Should find default registration key when no fiscal position is set",
        )
        self.assertEqual(
            order.verifactu_registration_key.code,
            "01",
            "Default registration key should have code '01'",
        )

    def test_pos_verifactu_journal_disabled(self):
        """Test POS order when journal is disabled for verifactu"""
        # Disable verifactu for the POS journal
        self.pos_config.journal_id.verifactu_enabled = False

        orders_data = [self._create_ui_order_data()]
        order_ids = self.env["pos.order"].create_from_ui(orders_data)
        order = self.env["pos.order"].browse(order_ids[0]["id"])

        # Should not be enabled even if company is enabled
        self.assertFalse(
            order.verifactu_enabled,
            "Order should not be verifactu enabled when journal is disabled",
        )

    def test_pos_verifactu_one2many_fields(self):
        """Test that One2many fields work correctly with verifactu entries"""
        orders_data = [self._create_ui_order_data()]
        order_ids = self.env["pos.order"].create_from_ui(orders_data)
        order = self.env["pos.order"].browse(order_ids[0]["id"])

        # Check that One2many fields exist and are accessible
        self.assertTrue(
            hasattr(order, "verifactu_invoice_entry_ids"),
            "Should have verifactu_invoice_entry_ids One2many field",
        )
        self.assertTrue(
            hasattr(order, "verifactu_response_line_ids"),
            "Should have verifactu_response_line_ids One2many field",
        )

        # Verifactu entries should be created automatically for verifactu orders
        self.assertGreater(
            len(order.verifactu_invoice_entry_ids),
            0,
            "Should have invoice entries for verifactu orders",
        )

        # Test the relationship: entry should reference back to this order
        entry = order.verifactu_invoice_entry_ids[0]
        self.assertEqual(
            entry.document_id,
            order.id,
            "Invoice entry should reference the correct order",
        )
        self.assertEqual(
            entry.model, "pos.order", "Invoice entry should have correct model"
        )

        # Response lines should initially be empty until sent to AEAT
        self.assertEqual(
            len(order.verifactu_response_line_ids),
            0,
            "Should have no response lines until sent to AEAT",
        )

    def test_pos_verifactu_resend_method(self):
        """Test resend_verifactu method exists and works"""
        orders_data = [self._create_ui_order_data()]
        order_ids = self.env["pos.order"].create_from_ui(orders_data)
        order = self.env["pos.order"].browse(order_ids[0]["id"])

        # Check method exists
        self.assertTrue(
            hasattr(order, "resend_verifactu"), "Should have resend_verifactu method"
        )

        # Should not error when called (even if conditions aren't met)
        try:
            order.resend_verifactu()
        except Exception as e:
            self.fail(f"resend_verifactu method should not raise exception: {e}")

    def test_pos_verifactu_write_protection(self):
        """Test write protection for sent orders"""
        orders_data = [self._create_ui_order_data()]
        order_ids = self.env["pos.order"].create_from_ui(orders_data)
        order = self.env["pos.order"].browse(order_ids[0]["id"])

        # Simulate order sent to verifactu
        order.aeat_state = "sent"

        # Should prevent changing protected fields
        with self.assertRaises(UserError):
            order.write({"pos_reference": "NEW_REF"})

    def test_pos_verifactu_cancel_method(self):
        """Test cancel_verifactu method exists"""
        orders_data = [self._create_ui_order_data()]
        order_ids = self.env["pos.order"].create_from_ui(orders_data)
        order = self.env["pos.order"].browse(order_ids[0]["id"])

        # Check method exists
        self.assertTrue(
            hasattr(order, "cancel_verifactu"), "Should have cancel_verifactu method"
        )

        # Should raise NotImplementedError
        with self.assertRaises(NotImplementedError):
            order.cancel_verifactu()

    def test_pos_verifactu_qr_values(self):
        """Test QR values dict structure for POS orders"""
        orders_data = [self._create_ui_order_data(amount=100)]
        order_ids = self.env["pos.order"].create_from_ui(orders_data)
        order = self.env["pos.order"].browse(order_ids[0]["id"])

        qr_values = order._get_verifactu_qr_values()

        self.assertEqual(
            list(qr_values.keys()), ["nif", "numserie", "fecha", "importe"]
        )
        self.assertEqual(
            qr_values["nif"], self.company.partner_id._parse_aeat_vat_info()[2]
        )
        self.assertEqual(qr_values["numserie"], "SIM/0001")
        self.assertEqual(qr_values["importe"], "121.00")

    def test_pos_verifactu_description_fallback(self):
        """Test verifactu description falls back to company description"""
        self.company.verifactu_description = "Company description"
        orders_data = [self._create_ui_order_data()]
        order_ids = self.env["pos.order"].create_from_ui(orders_data)
        order = self.env["pos.order"].browse(order_ids[0]["id"])

        # Order without its own description should fall back to company's
        self.assertFalse(order.verifactu_description)
        self.assertEqual(order._get_verifactu_description(), "Company description")

        # Order-level description takes precedence
        order.verifactu_description = "Order description"
        self.assertEqual(order._get_verifactu_description(), "Order description")

    def test_pos_verifactu_subsanacion_rechazo(self):
        """Test Subsanacion and RechazoPrevio flags in invoice dict"""
        orders_data = [self._create_ui_order_data()]
        order_ids = self.env["pos.order"].create_from_ui(orders_data)
        order = self.env["pos.order"].browse(order_ids[0]["id"])

        # sent_w_errors -> Subsanacion only
        order.aeat_state = "sent_w_errors"
        alta = order._get_verifactu_invoice_dict_out()["RegistroAlta"]
        self.assertEqual(alta.get("Subsanacion"), "S")
        self.assertNotIn("RechazoPrevio", alta)

        # incorrect -> Subsanacion + RechazoPrevio
        order.aeat_state = "incorrect"
        alta = order._get_verifactu_invoice_dict_out()["RegistroAlta"]
        self.assertEqual(alta.get("Subsanacion"), "S")
        self.assertEqual(alta.get("RechazoPrevio"), "X")

    def test_pos_verifactu_chaining_with_previous_entry(self):
        """Test chaining dict returns RegistroAnterior when there is a previous entry"""
        orders_data_1 = [self._create_ui_order_data(amount=100)]
        order_ids_1 = self.env["pos.order"].create_from_ui(orders_data_1)
        order_1 = self.env["pos.order"].browse(order_ids_1[0]["id"])

        orders_data_2 = [self._create_ui_order_data(amount=200)]
        order_ids_2 = self.env["pos.order"].create_from_ui(orders_data_2)
        order_2 = self.env["pos.order"].browse(order_ids_2[0]["id"])

        # Second order should reference first one via RegistroAnterior
        self.assertTrue(
            order_2.last_verifactu_invoice_entry_id.previous_invoice_entry_id,
            "Second order entry should link to a previous entry",
        )
        result = order_2._get_verifactu_chaining_invoice_dict()
        self.assertIn("RegistroAnterior", result)
        registro_anterior = result["RegistroAnterior"]
        self.assertEqual(
            registro_anterior["NumSerieFactura"],
            order_1._get_document_serial_number(),
        )
        self.assertEqual(registro_anterior["Huella"], order_1.verifactu_hash)

    def test_pos_verifactu_receiver_dict(self):
        """Test receiver dict generation for POS orders"""
        orders_data = [self._create_ui_order_data()]
        order_ids = self.env["pos.order"].create_from_ui(orders_data)
        order = self.env["pos.order"].browse(order_ids[0]["id"])

        receiver = order._get_verifactu_receiver_dict()
        self.assertEqual(receiver["NombreRazon"], self.partner.name)
        self.assertEqual(receiver["NIF"], self.partner._parse_aeat_vat_info()[2])

        # Without partner, receiver dict is empty
        order.partner_id = False
        self.assertEqual(order._get_verifactu_receiver_dict(), {})
