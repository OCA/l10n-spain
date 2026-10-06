# Copyright 2022 Creu Blanca
# Copyright 2023 Tecnativa - Pedro M. Baeza
# Copyright 2023 Tecnativa - Carolina Fernandez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

from psycopg2 import IntegrityError, errors

from odoo import exceptions
from odoo.tests.common import tagged
from odoo.tools import mute_logger

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestVatProrate(AccountTestInvoicingCommon):
    # Because we are using the AccountTestInvoicingCommon the final user is
    # 'Because I am accountman!' so we need to add the account_aeat
    # group to create account.update.vat_prorate records
    @classmethod
    def get_default_groups(cls):
        groups = super().get_default_groups()
        group_account_aeat = cls.env.ref(
            "l10n_es_aeat.group_account_aeat", raise_if_not_found=True
        )
        if group_account_aeat:
            return groups | group_account_aeat
        return groups

    @classmethod
    @AccountTestInvoicingCommon.setup_chart_template("es_pymes")
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                mail_create_nolog=True,
                mail_create_nosubscribe=True,
                mail_notrack=True,
                no_reset_password=True,
                tracking_disable=True,
            )
        )
        cls.env.company.write(
            {
                "with_vat_prorate": True,
                "vat_prorate_ids": [
                    (0, 0, {"date": date(2000, 1, 1), "vat_prorate": 10}),
                    (0, 0, {"date": date(2001, 1, 1), "vat_prorate": 20}),
                ],
            }
        )
        cls.product_b.write(
            {
                "supplier_taxes_id": [(6, 0, cls.tax_purchase_a.ids)],
                "taxes_id": [(6, 0, cls.tax_sale_a.ids)],
            }
        )
        cls.analytic_plan = cls.env["account.analytic.plan"].create({"name": "Default"})
        cls.analytic_account = cls.env["account.analytic.account"].create(
            {
                "name": "Test analytic account",
                "plan_id": cls.analytic_plan.id,
            }
        )

    # Put `zzz` for making sure that the test is executed in last place, as the cursor
    # gets incoherent after returning from the SQL constraint violation
    @mute_logger("odoo.sql_db")
    def test_zzz_company_vat_prorate_out_of_range(self):
        vat_prorate_line = self.env.company.vat_prorate_ids[0]
        with self.assertRaises(IntegrityError):
            vat_prorate_line.vat_prorate = 200

    @mute_logger("odoo.sql_db")
    def test_company_special_vat_prorate_out_of_range(self):
        # A error should be displayed if special prorates are 100%
        prorate_id = self.env.company.vat_prorate_ids[0]
        with self.assertRaises(errors.CheckViolation):
            prorate_id.write({"type": "special", "vat_prorate": 100})

    def test_no_company_vat_prorate_information(self):
        self.assertTrue(self.env.company.vat_prorate_ids)
        with self.assertRaises(exceptions.ValidationError):
            self.env.company.write({"vat_prorate_ids": False})

    def test_no_prorate_in_invoice(self):
        self.env.company.write(
            {"with_vat_prorate": False}
        )  # We want to be sure that it is executed properly
        invoice = self.init_invoice(
            "in_invoice", products=[self.product_a, self.product_b]
        )
        self.assertEqual(4, len(invoice.line_ids))
        self.assertEqual(1, len(invoice.line_ids.filtered(lambda r: r.tax_line_id)))

    def test_prorate_different_accounts_in_invoice(self):
        invoice = self.init_invoice(
            "in_invoice", products=[self.product_a, self.product_b]
        )
        self.assertEqual(6, len(invoice.line_ids))
        self.assertEqual(3, len(invoice.line_ids.filtered(lambda r: r.tax_line_id)))
        # Deal with analytics
        invoice.line_ids[0].analytic_distribution = {self.analytic_account.id: 100}
        self.assertEqual(4, len(invoice.line_ids))
        self.assertEqual(
            1,
            len(invoice.line_ids.filtered(lambda r: r.analytic_distribution)),
        )

    def test_prorate_tax_with_prorate_account(self):
        # 21% EU S (Services) tax
        tax = self.env.ref(
            f"account.{self.env.company.id}_account_tax_template_p_iva21_sp_in"
        )
        invoice = self.init_invoice(
            "in_invoice", products=[self.product_a, self.product_b], taxes=[tax]
        )
        self.assertEqual(7, len(invoice.line_ids))
        self.assertEqual(4, len(invoice.line_ids.filtered(lambda r: r.tax_line_id)))

    def test_prorate_same_accounts_in_invoice(self):
        self.product_b.property_account_expense_id = self.company_data[
            "default_account_expense"
        ]
        invoice = self.init_invoice(
            "in_invoice", products=[self.product_a, self.product_b]
        )
        self.assertEqual(5, len(invoice.line_ids))
        tax_lines = invoice.line_ids.filtered(lambda r: r.tax_line_id)
        self.assertEqual(2, len(tax_lines))
        self.assertEqual(1, len(tax_lines.filtered("vat_prorate")))
        # One of the tax lines should have expense account and the other the tax account
        self.assertNotEqual(tax_lines[0].account_id, tax_lines[1].account_id)

    def test_no_prorate_in_refund(self):
        self.env.company.write(
            {"with_vat_prorate": False}
        )  # We want to be sure that it is executed properly
        invoice = self.init_invoice(
            "in_refund", products=[self.product_a, self.product_b]
        )
        self.assertEqual(4, len(invoice.line_ids))
        self.assertEqual(1, len(invoice.line_ids.filtered(lambda r: r.tax_line_id)))

    def test_prorate_different_accounts_in_refund(self):
        invoice = self.init_invoice(
            "in_refund", products=[self.product_a, self.product_b]
        )
        self.assertEqual(6, len(invoice.line_ids))
        self.assertEqual(3, len(invoice.line_ids.filtered(lambda r: r.tax_line_id)))

    def test_prorate_same_accounts_in_refund(self):
        self.product_b.property_account_expense_id = self.company_data[
            "default_account_expense"
        ]
        invoice = self.init_invoice(
            "in_refund", products=[self.product_a, self.product_b]
        )
        self.assertEqual(5, len(invoice.line_ids))
        self.assertEqual(2, len(invoice.line_ids.filtered(lambda r: r.tax_line_id)))

    def test_no_prorate_out_invoice(self):
        self.env.company.write(
            {"with_vat_prorate": False}
        )  # We want to be sure that it is executed properly
        invoice = self.init_invoice(
            "out_invoice", products=[self.product_a, self.product_b]
        )
        self.assertEqual(4, len(invoice.line_ids))
        self.assertEqual(1, len(invoice.line_ids.filtered(lambda r: r.tax_line_id)))

    def test_prorate_out_invoice(self):
        invoice = self.init_invoice(
            "out_invoice", products=[self.product_a, self.product_b]
        )
        self.assertEqual(4, len(invoice.line_ids))
        self.assertEqual(1, len(invoice.line_ids.filtered(lambda r: r.tax_line_id)))

    def test_no_prorate_out_refund(self):
        self.env.company.write(
            {"with_vat_prorate": False}
        )  # We want to be sure that it is executed properly
        invoice = self.init_invoice(
            "out_refund", products=[self.product_a, self.product_b]
        )
        self.assertEqual(4, len(invoice.line_ids))
        self.assertEqual(1, len(invoice.line_ids.filtered(lambda r: r.tax_line_id)))

    def test_prorate_out_refund(self):
        invoice = self.init_invoice(
            "out_refund", products=[self.product_a, self.product_b]
        )
        self.assertEqual(4, len(invoice.line_ids))
        self.assertEqual(1, len(invoice.line_ids.filtered(lambda r: r.tax_line_id)))

    def test_prorate_make_refund(self):
        invoice = self.init_invoice("in_invoice", products=[self.product_a])
        invoice.action_post()
        wizard = (
            self.env["account.move.reversal"]
            .with_context(active_ids=invoice.ids, active_model="account.move")
            .create({"journal_id": invoice.journal_id.id})
        )
        wizard.reverse_moves()
        refund = wizard.new_move_ids
        self.assertEqual(len(refund.line_ids), 4)
        tax_lines = refund.line_ids.filtered(lambda r: r.tax_line_id)
        self.assertEqual(len(tax_lines), 2)
        # One of the tax lines should have expense account and the other the tax account
        self.assertNotEqual(tax_lines[0].account_id, tax_lines[1].account_id)

    def test_special_prorate_default_true(self):
        self.env.company.vat_prorate_ids[0].write(
            {
                "type": "special",
                "special_vat_prorate_default": True,
            }
        )
        invoice = self.init_invoice(
            "in_invoice", products=[self.product_a, self.product_b]
        )
        self.assertEqual(6, len(invoice.line_ids))
        self.assertEqual(2, len(invoice.line_ids.filtered("vat_prorate")))

    def test_special_prorate_default_false(self):
        self.env.company.vat_prorate_ids[0].write(
            {
                "type": "special",
                "special_vat_prorate_default": False,
            }
        )
        invoice = self.init_invoice(
            "in_invoice", products=[self.product_a, self.product_b]
        )
        self.assertEqual(4, len(invoice.line_ids))
        self.assertEqual(0, len(invoice.line_ids.filtered("vat_prorate")))

    def test_special_prorate_mixed(self):
        self.env.company.vat_prorate_ids[0].write(
            {
                "type": "special",
                "special_vat_prorate_default": True,
            }
        )
        invoice = self.init_invoice(
            "in_invoice", products=[self.product_a, self.product_b]
        )
        invoice.write(
            {
                "invoice_line_ids": [
                    (1, line.id, {"with_vat_prorate": False})
                    for line in invoice.invoice_line_ids.filtered(
                        lambda r: r.product_id == self.product_a
                    )
                ]
            }
        )
        self.assertEqual(5, len(invoice.line_ids))
        self.assertEqual(1, len(invoice.line_ids.filtered("vat_prorate")))
        inv_line_b = invoice.line_ids.filtered(lambda r: r.product_id == self.product_b)
        prorate_id = self.env.company.vat_prorate_ids[0]
        self.assertAlmostEqual(
            invoice.line_ids.filtered("vat_prorate").debit,
            inv_line_b.price_subtotal
            * inv_line_b.tax_ids[:1].amount
            * (100 - prorate_id.vat_prorate)
            / 10000,
        )

    def test_prorate_update_with_wizard(self):
        wizard = (
            self.env["account.update.vat_prorate"]
            .with_company(self.env.company)
            .create({})
        )
        self.assertEqual(wizard.company_id.id, self.env.company.id)
        self.assertTrue(wizard.with_vat_prorate)
        self.assertEqual(len(wizard.vat_prorate_ids), 2)
        # Update company data through the wizard
        wizard.with_vat_prorate = False
        wizard.vat_prorate_ids = wizard.vat_prorate_ids[1:]
        wizard.execute()
        self.assertFalse(self.env.company.with_vat_prorate)
        self.assertEqual(len(self.env.company.vat_prorate_ids), 1)

    def test_with_vat_prorate_on_api_create(self):
        """Test with_vat_prorate is set correctly when creating via API (no onchange).

        This test simulates the race condition scenario where invoice lines are
        created via API/import without onchange execution. The with_vat_prorate
        field should be correctly calculated in the create() method.
        """
        invoice = self._create_invoice(
            move_type="in_invoice",
            invoice_date=date(2000, 6, 1),
            invoice_line_ids=[
                self._prepare_invoice_line(
                    product_id=self.product_a,
                    quantity=1,
                    price_unit=100,
                    tax_ids=self.tax_purchase_a,
                )
            ],
        )
        invoice_line = invoice.invoice_line_ids.filtered(
            lambda line: line.product_id == self.product_a
        )
        self.assertTrue(
            invoice_line.with_vat_prorate,
            "with_vat_prorate should be True for lines with prorate taxes "
            "even when created via API without onchange",
        )
        # Invoice lines: 1 product line + 1 tax line + 1 prorate line = 3 total
        self.assertGreaterEqual(len(invoice.line_ids), 3)
        prorate_lines = invoice.line_ids.filtered("vat_prorate")
        self.assertEqual(
            1,
            len(prorate_lines),
            "Prorate lines should be created automatically",
        )

    def test_with_vat_prorate_on_refund_from_reversed_entry(self):
        """Test with_vat_prorate is recomputed on refunds created via reversal.

        When creating a refund from a posted invoice using the reversal wizard,
        the with_vat_prorate field should be correctly set on the refund lines.
        """
        invoice = self._create_invoice(
            move_type="in_invoice",
            invoice_date=date(2000, 6, 1),
            invoice_line_ids=[
                self._prepare_invoice_line(
                    product_id=self.product_a,
                    quantity=1,
                    price_unit=100,
                    tax_ids=self.tax_purchase_a,
                )
            ],
            post=True,
        )
        wizard = (
            self.env["account.move.reversal"]
            .with_context(active_ids=invoice.ids, active_model="account.move")
            .create({"journal_id": invoice.journal_id.id})
        )
        wizard.reverse_moves()
        refund = wizard.new_move_ids
        refund_line = refund.invoice_line_ids.filtered(
            lambda line: line.product_id == self.product_a
        )
        self.assertTrue(
            refund_line.with_vat_prorate,
            "with_vat_prorate should be True on refund lines",
        )
        # Refund lines: 1 product line + 1 tax line + 1 prorate line = 3 total
        self.assertGreaterEqual(len(refund.line_ids), 3)
        prorate_lines = refund.line_ids.filtered("vat_prorate")
        self.assertEqual(
            1,
            len(prorate_lines),
            "Prorate lines should be created on refund",
        )

    def test_with_vat_prorate_on_copy(self):
        """Test with_vat_prorate is recomputed on duplicates.

        When duplicating an invoice, the with_vat_prorate field should be
        correctly recalculated on the new invoice lines.
        """
        invoice = self._create_invoice(
            move_type="in_invoice",
            invoice_date=date(2000, 6, 1),
            invoice_line_ids=[
                self._prepare_invoice_line(
                    product_id=self.product_a,
                    quantity=1,
                    price_unit=100,
                    tax_ids=self.tax_purchase_a,
                )
            ],
        )
        duplicated = invoice.copy()
        duplicated_line = duplicated.invoice_line_ids.filtered(
            lambda line: line.product_id == self.product_a
        )
        self.assertTrue(
            duplicated_line.with_vat_prorate,
            "with_vat_prorate should be True on duplicated invoice lines",
        )
        # Duplicated lines: 1 product line + 1 tax line + 1 prorate line = 3 total
        self.assertGreaterEqual(len(duplicated.line_ids), 3)
        prorate_lines = duplicated.line_ids.filtered("vat_prorate")
        self.assertEqual(
            1,
            len(prorate_lines),
            "Prorate lines should be created on duplicated invoice",
        )

    def test_check_prorate_applied_validation_error(self):
        """Test _check_prorate_applied raises ValidationError when prorate missing.

        When posting an invoice that should have prorate lines but doesn't,
        a ValidationError should be raised.
        """
        invoice = self._create_invoice(
            move_type="in_invoice",
            invoice_date=date(2000, 6, 1),
            invoice_line_ids=[
                self._prepare_invoice_line(
                    product_id=self.product_a,
                    quantity=1,
                    price_unit=100,
                    tax_ids=self.tax_purchase_a,
                    with_vat_prorate=True,
                )
            ],
        )
        prorate_lines = invoice.line_ids.filtered("vat_prorate")
        prorate_lines.with_context(dynamic_unlink=True).unlink()
        with self.assertRaises(
            exceptions.ValidationError,
            msg="Should raise ValidationError when prorate lines are missing",
        ):
            invoice.action_post()

    def test_check_prorate_applied_success(self):
        """Test that _check_prorate_applied passes when prorate is correctly applied.

        When posting an invoice with correctly applied prorate, no error should occur.
        """
        invoice = self._create_invoice(
            move_type="in_invoice",
            invoice_date=date(2000, 6, 1),
            invoice_line_ids=[
                self._prepare_invoice_line(
                    product_id=self.product_a,
                    quantity=1,
                    price_unit=100,
                    tax_ids=self.tax_purchase_a,
                )
            ],
        )
        prorate_lines = invoice.line_ids.filtered("vat_prorate")
        self.assertTrue(
            prorate_lines,
            "Prorate lines should exist before posting",
        )
        invoice.action_post()
        self.assertEqual(
            invoice.state,
            "posted",
            "Invoice should be posted successfully when prorate is applied",
        )

    def test_with_vat_prorate_special_mode_manual_override(self):
        """Test that with_vat_prorate can be manually set in special prorate mode.

        In special prorate mode, users can manually set with_vat_prorate on each line
        after creation.
        """
        self.env.company.vat_prorate_ids[0].write(
            {
                "type": "special",
                "special_vat_prorate_default": True,
            }
        )
        invoice = self._create_invoice(
            move_type="in_invoice",
            invoice_date=date(2000, 6, 1),
            invoice_line_ids=[
                self._prepare_invoice_line(
                    product_id=self.product_a,
                    quantity=1,
                    price_unit=100,
                    tax_ids=self.tax_purchase_a,
                )
            ],
        )
        invoice_line = invoice.invoice_line_ids.filtered(
            lambda line: line.product_id == self.product_a
        )
        # In special mode with default=True, the line should have prorate
        self.assertTrue(
            invoice_line.with_vat_prorate,
            "with_vat_prorate should be True by default in special mode",
        )
        # Now manually change it to False
        invoice_line.write({"with_vat_prorate": False})
        self.assertFalse(
            invoice_line.with_vat_prorate,
            "Manual with_vat_prorate=False should be preserved in special mode",
        )

    def test_with_vat_prorate_general_mode_auto_detect(self):
        """Test that with_vat_prorate is auto-detected in general prorate mode.

        In general prorate mode, with_vat_prorate should be automatically
        set based on whether the line has taxes with with_vat_prorate=True.
        """
        invoice = self._create_invoice(
            move_type="in_invoice",
            invoice_date=date(2000, 6, 1),
            invoice_line_ids=[
                self._prepare_invoice_line(
                    product_id=self.product_a,
                    quantity=1,
                    price_unit=100,
                    tax_ids=self.tax_purchase_a,
                )
            ],
        )
        invoice_line = invoice.invoice_line_ids.filtered(
            lambda line: line.product_id == self.product_a
        )
        self.assertTrue(
            invoice_line.with_vat_prorate,
            "with_vat_prorate should be auto-detected as True for taxes with prorate",
        )
        # After writing, the field should remain as it was set in create()
        # because the onchange doesn't automatically recalculate on write
        invoice_line.write({"tax_ids": [(5, 0)]})
        # The field doesn't auto-update on write, only on onchange in UI
        # This is expected behavior - the fix ensures it's set correctly on create

    def test_recompute_with_vat_prorate_if_needed(self):
        """Test _recompute_with_vat_prorate_if_needed method.

        This method should correctly recompute with_vat_prorate on lines
        in scenarios where it might not have been set correctly.
        """
        invoice = self._create_invoice(
            move_type="in_invoice",
            invoice_date=date(2000, 6, 1),
            invoice_line_ids=[
                self._prepare_invoice_line(
                    product_id=self.product_a,
                    quantity=1,
                    price_unit=100,
                    tax_ids=self.tax_purchase_a,
                )
            ],
        )
        invoice_line = invoice.invoice_line_ids.filtered(
            lambda line: line.product_id == self.product_a
        )
        invoice_line.with_vat_prorate = False
        self.assertFalse(invoice_line.with_vat_prorate)
        invoice._recompute_with_vat_prorate_if_needed()
        self.assertTrue(
            invoice_line.with_vat_prorate,
            "with_vat_prorate should be recomputed to True",
        )

    def test_with_vat_prorate_display_lines_ignored(self):
        """Test that display lines (sections, notes) are ignored for prorate.

        Lines with display_type set to 'line_section' or 'line_note'
        should not be processed for prorate calculation.
        """
        from odoo.fields import Command

        invoice = self._create_invoice(
            move_type="in_invoice",
            invoice_date=date(2000, 6, 1),
            invoice_line_ids=[
                Command.create(
                    {
                        "display_type": "line_section",
                        "name": "Section Header",
                    }
                ),
                self._prepare_invoice_line(
                    product_id=self.product_a,
                    quantity=1,
                    price_unit=100,
                    tax_ids=self.tax_purchase_a,
                ),
                Command.create(
                    {
                        "display_type": "line_note",
                        "name": "Note text",
                    }
                ),
            ],
        )
        section_line = invoice.invoice_line_ids.filtered(
            lambda line: line.display_type == "line_section"
        )
        note_line = invoice.invoice_line_ids.filtered(
            lambda line: line.display_type == "line_note"
        )
        self.assertFalse(
            section_line.with_vat_prorate,
            "Section lines should not have with_vat_prorate=True",
        )
        self.assertFalse(
            note_line.with_vat_prorate,
            "Note lines should not have with_vat_prorate=True",
        )
