# Copyright 2024
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError

# Inherit the official PoS base test
from odoo.addons.point_of_sale.tests.test_point_of_sale import TestPointOfSale


class TestL10nEsPosOca(TestPointOfSale):
    def setUp(self):
        super().setUp()

        # Ensure simplified partner template exists (functional dependency)
        self.env.ref("l10n_es.partner_simplified")

        # Build a minimal PoS config for company1 (no demo xmlids)
        self.pos_config = self._create_min_pos_config_for_company(self.company1)

        # Enable module settings under test
        self.pos_config.write(
            {
                "iface_l10n_es_simplified_invoice": True,
                "l10n_es_simplified_invoice_limit": 100,
            }
        )
        self.sequence = self.pos_config.l10n_es_simplified_invoice_sequence_id

        # Create a PoS session for this config
        self.pos_session = self.env["pos.session"].create(
            {"config_id": self.pos_config.id}
        )

        # Local partner (avoid demo data)
        self.partner = self.env["res.partner"].create(
            {"name": "Test Partner", "email": "test@example.com"}
        )

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------

    def _create_min_pos_config_for_company(self, company):
        """Create a minimal pos.config for the given company (Odoo 18 compatible)."""
        pos_config = self.env["pos.config"]

        # Warehouse / outgoing picking type (required by PoS)
        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", company.id)], limit=1
        )
        if not warehouse:
            warehouse = self.env["stock.warehouse"].create(
                {
                    "name": f"WH {company.name}",
                    "code": f"W{company.id}",
                    "company_id": company.id,
                }
            )
        picking_type = warehouse.out_type_id

        # A company-specific active pricelist (the base test deactivates existing ones)
        pricelist = self.env["product.pricelist"].search(
            [("company_id", "=", company.id), ("active", "=", True)], limit=1
        )
        if not pricelist:
            pricelist = self.env["product.pricelist"].create(
                {
                    "name": f"{company.name} pricelist",
                    "currency_id": company.currency_id.id,
                    "company_id": company.id,
                    "sequence": 1,
                    "active": True,
                }
            )

        # Sales journal
        sale_journal = self.env["account.journal"].search(
            [("type", "=", "sale"), ("company_id", "=", company.id)],
            limit=1,
        )
        if not sale_journal:
            sale_journal = self.env["account.journal"].create(
                {
                    "name": "POS Sales",
                    "code": "POSS",
                    "type": "sale",
                    "company_id": company.id,
                }
            )

        # Receivable account (Odoo 18+: account_type + company_ids m2m)
        receivable = self.env["account.account"].search(
            [
                ("account_type", "=", "asset_receivable"),
                ("deprecated", "=", False),
                ("company_ids", "in", [company.id]),
            ],
            limit=1,
        )
        if not receivable:
            receivable = self.env["account.account"].create(
                {
                    "name": "Debtors",
                    "code": "430000",
                    "account_type": "asset_receivable",
                    "reconcile": True,
                    "company_ids": [(6, 0, [company.id])],
                }
            )

        # PoS payment method
        payment_method = self.env["pos.payment.method"].create(
            {
                "name": "Test PM",
                "receivable_account_id": receivable.id,
                "is_cash_count": True,
                "company_id": company.id,
            }
        )

        vals = {
            "name": f"Test POS {company.name}",
            "company_id": company.id,
            "picking_type_id": picking_type.id,
            "available_pricelist_ids": [(6, 0, [pricelist.id])],
            "pricelist_id": pricelist.id,
            "invoice_journal_id": sale_journal.id,
        }
        if "payment_method_ids" in pos_config._fields:
            vals["payment_method_ids"] = [(6, 0, [payment_method.id])]
        return pos_config.create(vals)

    # ---------------------------------------------------------------------
    # Tests (module-specific)
    # ---------------------------------------------------------------------

    def test_ir_sequence_constraint(self):
        """Copying a sequence with same prefix must fail (business rule)."""
        self.assertTrue(self.sequence, "Sequence should exist for simplified invoices.")
        with self.assertRaises(UserError):
            self.sequence.copy({"prefix": self.sequence.prefix})

    def test_pos_config_creation(self):
        """Sequence exists and its prefix equals config name"""
        self.assertTrue(self.pos_config.l10n_es_simplified_invoice_sequence_id)
        self.assertEqual(
            self.pos_config.l10n_es_simplified_invoice_sequence_id.prefix,
            self.pos_config.name,
        )

    def test_pos_config_copy(self):
        """Copying a config creates a different sequence."""
        new_cfg = self.pos_config.copy()
        self.assertNotEqual(
            new_cfg.l10n_es_simplified_invoice_sequence_id,
            self.pos_config.l10n_es_simplified_invoice_sequence_id,
        )

    def test_pos_config_write(self):
        """Renaming the config updates the sequence prefix accordingly"""
        self.pos_config.write({"name": "New Name"})
        self.assertEqual(
            self.pos_config.l10n_es_simplified_invoice_sequence_id.prefix,
            "New Name",
        )

    def test_pos_config_unlink(self):
        """Unlink config removes its sequence; must free FK from session first."""
        seq = self.pos_config.l10n_es_simplified_invoice_sequence_id
        # Drop the session first to satisfy FK constraint
        self.pos_session.unlink()
        self.pos_config.unlink()
        self.assertFalse(seq.exists())

    def test_pos_order_simplified_invoice(self):
        """Create a simplified-invoice order within the limit."""
        order = self.env["pos.order"].create(
            {
                "session_id": self.pos_session.id,
                "partner_id": self.partner.id,
                "amount_total": 50,
                "amount_tax": 0,
                "amount_paid": 50,
                "amount_return": 0,
                "to_invoice": False,
                "l10n_es_simplified_number": 1,
                "is_l10n_es_simplified_invoice": True,
                "l10n_es_unique_id": "S0001",
            }
        )
        self.assertTrue(order.is_l10n_es_simplified_invoice)
        self.assertEqual(order.l10n_es_unique_id, "S0001")

    # ---------------------------------------------------------------------
    # Additional tests for better coverage
    # ---------------------------------------------------------------------

    def test_pos_config_compute_simplified_invoice_sequence(self):
        """Test computed fields for simplified invoice sequence."""
        # Test sequence computation
        self.pos_config._compute_simplified_invoice_sequence()

        # Verify computed fields are set correctly
        self.assertTrue(self.pos_config.l10n_es_simplified_invoice_number)
        self.assertTrue(self.pos_config.l10n_es_simplified_invoice_prefix)
        self.assertTrue(self.pos_config.l10n_es_simplified_invoice_padding)

        # Test with modified sequence
        self.sequence.write({"prefix": "TEST_", "padding": 6})
        self.pos_config._compute_simplified_invoice_sequence()
        self.assertEqual(self.pos_config.l10n_es_simplified_invoice_prefix, "TEST_")
        self.assertEqual(self.pos_config.l10n_es_simplified_invoice_padding, 6)

    def test_pos_config_compute_simplified_config(self):
        """Test simplified config computation."""
        # Test when simplified invoice is enabled
        self.pos_config.iface_l10n_es_simplified_invoice = True
        self.pos_config._compute_simplified_config()
        self.assertTrue(self.pos_config.is_simplified_config)

        # Test when simplified invoice is disabled
        self.pos_config.iface_l10n_es_simplified_invoice = False
        self.pos_config._compute_simplified_config()
        self.assertFalse(self.pos_config.is_simplified_config)

    def test_pos_config_compute_simplified_partner_id(self):
        """Test simplified partner computation."""
        self.pos_config._compute_simplified_partner_id()

        # Should reference the l10n_es simplified partner
        expected_partner = self.env.ref("l10n_es.partner_simplified")
        self.assertEqual(self.pos_config.simplified_partner_id, expected_partner)

    def test_pos_config_onchange_simplified_invoice(self):
        """Test onchange method for simplified invoice."""
        # Create config without invoice journal
        pos_config = self.env["pos.config"].create(
            {
                "name": "Test Onchange Config",
                "company_id": self.company1.id,
                "picking_type_id": self.pos_config.picking_type_id.id,
                "pricelist_id": self.pos_config.pricelist_id.id,
            }
        )

        # Clear invoice journal
        pos_config.invoice_journal_id = False

        # Enable simplified invoice
        pos_config.iface_l10n_es_simplified_invoice = True
        pos_config._onchange_l10n_iface_l10n_es_simplified_invoice()

        # Should set invoice journal
        self.assertTrue(pos_config.invoice_journal_id)

    def test_pos_config_get_default_methods(self):
        """Test default value getter methods."""
        # Test default padding
        padding = self.pos_config._get_default_padding()
        self.assertTrue(isinstance(padding, int | str))

        # Test default prefix
        prefix = self.pos_config._get_default_prefix()
        self.assertTrue(isinstance(prefix, str))

        # Test sequence name translation
        name = self.pos_config._get_l10n_es_sequence_name()
        self.assertIn("Simplified Invoice", name)

    def test_pos_config_create_with_duplicate_prefix(self):
        """Test creating config with duplicate prefix handling."""
        # Create config with same name to test prefix conflict resolution
        new_config = self.env["pos.config"].create(
            {
                "name": self.pos_config.name,
                "company_id": self.company1.id,
                "picking_type_id": self.pos_config.picking_type_id.id,
                "pricelist_id": self.pos_config.pricelist_id.id,
            }
        )

        # Should have different sequence with modified prefix
        self.assertNotEqual(
            new_config.l10n_es_simplified_invoice_sequence_id,
            self.pos_config.l10n_es_simplified_invoice_sequence_id,
        )
        self.assertNotEqual(
            new_config.l10n_es_simplified_invoice_prefix,
            self.pos_config.l10n_es_simplified_invoice_prefix,
        )

    def test_pos_order_simplified_limit_check(self):
        """Test simplified invoice limit checking."""
        pos_order_model = self.env["pos.order"]

        # Test amounts within limit
        self.assertTrue(pos_order_model._simplified_limit_check(50, 100))
        self.assertFalse(
            pos_order_model._simplified_limit_check(100, 100)
        )  # 100 is equal to limit, should be false

        # Test amounts over limit
        self.assertFalse(pos_order_model._simplified_limit_check(150, 100))

        # Test with default limit
        self.assertTrue(pos_order_model._simplified_limit_check(2500))  # Under 3000
        self.assertFalse(pos_order_model._simplified_limit_check(3500))  # Over 3000

    def test_pos_order_update_sequence_number(self):
        """Test sequence number update."""
        pos_order_model = self.env["pos.order"]
        initial_number = self.sequence.number_next_actual

        pos_order_model._update_sequence_number(self.pos_config)

        # Refresh sequence to get updated value
        self.sequence.invalidate_recordset(["number_next_actual"])
        # Sequence should be incremented
        self.assertEqual(self.sequence.number_next_actual, initial_number + 1)

    def test_res_config_settings_related_fields(self):
        """Test ResConfigSettings related fields."""
        # Create settings instance
        config_settings = self.env["res.config.settings"].create(
            {
                "pos_config_id": self.pos_config.id,
            }
        )

        # Test related fields work correctly
        self.assertEqual(
            config_settings.pos_iface_l10n_es_simplified_invoice,
            self.pos_config.iface_l10n_es_simplified_invoice,
        )
        self.assertEqual(
            config_settings.pos_l10n_es_simplified_invoice_limit,
            self.pos_config.l10n_es_simplified_invoice_limit,
        )
        self.assertEqual(
            config_settings.pos_l10n_es_simplified_invoice_sequence_id,
            self.pos_config.l10n_es_simplified_invoice_sequence_id,
        )
        self.assertEqual(
            config_settings.pos_l10n_es_simplified_invoice_prefix,
            self.pos_config.l10n_es_simplified_invoice_prefix,
        )

        # Test writing to related fields
        config_settings.write(
            {
                "pos_l10n_es_simplified_invoice_limit": 500,
            }
        )
        self.assertEqual(self.pos_config.l10n_es_simplified_invoice_limit, 500)

    def test_ir_sequence_constraint_edge_cases(self):
        """Test sequence constraints with edge cases."""
        # Test constraint with copy context (should not raise)
        sequence_copy = self.sequence.with_context(copy_pos_config=True)
        # This should not raise an error due to context
        try:
            sequence_copy.check_simplified_invoice_unique_prefix()
        except UserError:
            self.fail("Constraint should not raise with copy_pos_config context")

        # Test with different code (should not raise)
        other_sequence = self.env["ir.sequence"].create(
            {
                "name": "Other Sequence",
                "code": "other.code",
                "prefix": self.sequence.prefix,  # Same prefix but different code
            }
        )
        try:
            other_sequence.check_simplified_invoice_unique_prefix()
        except UserError:
            self.fail("Constraint should not raise for different sequence code")
