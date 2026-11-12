# Copyright 2026 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import importlib.util

from odoo.tests import tagged
from odoo.tools.misc import file_path

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestL10nEsReav(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_chart_template("es_pymes")
    def setUpClass(cls):
        super().setUpClass()
        ChartTemplate = cls.env["account.chart.template"]
        cls.tax_p_reav = ChartTemplate.ref("account_tax_template_p_reav0")
        cls.tax_s_reav = ChartTemplate.ref("account_tax_template_s_reav0")
        cls.fp_reav = ChartTemplate.ref("fp_reav")
        cls.partner_a.property_account_position_id = cls.fp_reav

    def test_reav_on_customer_invoice(self):
        invoice = self.init_invoice(
            "out_invoice", partner=self.partner_a, products=self.product_a
        )
        self.assertEqual(invoice.fiscal_position_id, self.fp_reav)
        self.assertEqual(invoice.invoice_line_ids.tax_ids, self.tax_s_reav)
        self.assertEqual(invoice.l10n_es_regime_code, "05")

    def test_reav_on_vendor_bill(self):
        bill = self.init_invoice(
            "in_invoice", partner=self.partner_a, products=self.product_a
        )
        self.assertEqual(bill.fiscal_position_id, self.fp_reav)
        self.assertEqual(bill.invoice_line_ids.tax_ids, self.tax_p_reav)
        self.assertEqual(bill.l10n_es_regime_code, "05")

    def test_reav_taxes_are_vat(self):
        """The REAV taxes are VAT ones (VERI*FACTU tax 01), with the travel
        agencies regime code. The VAT of the purchases for the trip is not
        deductible (art. 146 LIVA)."""
        for tax in self.tax_p_reav | self.tax_s_reav:
            self.assertEqual(tax.l10n_es_applicability, "01")
            self.assertEqual(tax.l10n_es_regime_code, "05")
        self.assertEqual(self.tax_p_reav.l10n_es_type, "no_deducible")
        self.assertEqual(self.tax_s_reav.l10n_es_type, "sujeto")

    def test_only_the_reav_fiscal_position(self):
        """The module adds only the REAV fiscal position, without country, so it
        never becomes the domestic one of the company."""
        positions = self.env["account.fiscal.position"].search(
            [("company_id", "=", self.env.company.id)]
        )
        reav_positions = positions.filtered(
            lambda position: "reav" in position.get_external_id()[position.id]
        )
        self.assertEqual(reav_positions, self.fp_reav)
        self.assertFalse(self.fp_reav.country_id)
        self.assertNotEqual(self.env.company.domestic_fiscal_position_id, self.fp_reav)

    def _product_with_taxes(self, sale_tax, purchase_tax):
        ChartTemplate = self.env["account.chart.template"]
        return self.product_a.copy(
            {
                "taxes_id": [
                    (6, 0, ChartTemplate.ref(f"account_tax_template_{sale_tax}").ids)
                ],
                "supplier_taxes_id": [
                    (
                        6,
                        0,
                        ChartTemplate.ref(f"account_tax_template_{purchase_tax}").ids,
                    )
                ],
            }
        )

    def test_reav_other_rates(self):
        """The VAT of any rate is replaced, not only the 21 %: with the
        REAV position a tax that is not replaced would be removed. The 5 % is
        archived by the chart and is used once activated."""
        ChartTemplate = self.env["account.chart.template"]
        for xmlid in ("s_iva5s", "p_iva5_bc"):
            ChartTemplate.ref(f"account_tax_template_{xmlid}").active = True
        products = self._product_with_taxes(
            "s_iva10b", "p_iva10_sc"
        ) | self._product_with_taxes("s_iva0b", "p_iva0_s_bc")
        products |= self._product_with_taxes("s_iva0s", "p_iva10_nd")
        products |= self._product_with_taxes("s_iva5s", "p_iva5_bc")
        invoice = self.init_invoice(
            "out_invoice", partner=self.partner_a, products=products
        )
        for line in invoice.invoice_line_ids:
            self.assertEqual(line.tax_ids, self.tax_s_reav)
        bill = self.init_invoice(
            "in_invoice", partner=self.partner_a, products=products
        )
        for line in bill.invoice_line_ids:
            self.assertEqual(line.tax_ids, self.tax_p_reav)

    def test_reav_keeps_taxes_outside_the_regime(self):
        """The investment goods of the agency and its own exempt supplies are
        outside the REAV (art. 146 LIVA): the REAV position keeps their taxes,
        and the domestic position of the chart too."""
        ChartTemplate = self.env["account.chart.template"]
        ChartTemplate.ref("account_tax_template_s_iva0_art23").active = True
        taxes = {
            "s_iva0_nsd": "p_iva21_bi",
            "s_iva0_art23": "p_iva10_bi",
        }
        products = self.env["product.product"]
        for sale_tax, purchase_tax in taxes.items():
            products |= self._product_with_taxes(sale_tax, purchase_tax)
        products.standard_price = 1000
        invoice = self.init_invoice(
            "out_invoice", partner=self.partner_a, products=products
        )
        bill = self.init_invoice(
            "in_invoice", partner=self.partner_a, products=products
        )
        domestic = ChartTemplate.ref("l10n_es_domestic_fiscal_position")
        for move, xmlids in ((invoice, taxes.keys()), (bill, taxes.values())):
            self.assertEqual(move.fiscal_position_id, self.fp_reav)
            for line, xmlid in zip(move.invoice_line_ids, xmlids, strict=True):
                tax = ChartTemplate.ref(f"account_tax_template_{xmlid}")
                self.assertEqual(line.tax_ids, tax)
                self.assertIn(domestic, tax.fiscal_position_ids)
        # The investment goods keep their deductible VAT: 21 % and 10 % of 1000
        self.assertAlmostEqual(bill.amount_tax, 310)

    def test_reav_tax_without_reav_position(self):
        """A REAV tax put on a product only applies with the REAV position"""
        product = self.product_a.copy({"taxes_id": [(6, 0, self.tax_s_reav.ids)]})
        invoice = self.init_invoice(
            "out_invoice", partner=self.partner_b, products=product
        )
        self.assertNotEqual(invoice.fiscal_position_id, self.fp_reav)
        self.assertFalse(invoice.invoice_line_ids.tax_ids)

    def _run_migration(self):
        script = file_path("l10n_es_reav/migrations/20.0.1.0.0/post-migration.py")
        spec = importlib.util.spec_from_file_location(
            "odoo.addons.l10n_es_reav.migrations.post_migration", script
        )
        post_migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(post_migration)
        # Without the frame of the Odoo migration manager that its decorator
        # inspects
        post_migration.migrate.__wrapped__(self.env, "18.0.1.0.0")

    def test_migration(self):
        """The migration from 18.0 fills the regime code and the applicability
        of the REAV taxes without changing a value already set, makes the REAV
        purchase tax not deductible, gives the REAV position the taxes it
        keeps, makes the REAV taxes replace the VAT of every rate, and warns
        about the products with REAV taxes"""
        self.env.cr.execute(
            """UPDATE account_tax SET l10n_es_regime_code = NULL,
               l10n_es_applicability = NULL WHERE id = %s""",
            [self.tax_s_reav.id],
        )
        self.env.cr.execute(
            """UPDATE account_tax SET l10n_es_regime_code = '01',
               l10n_es_type = 'sujeto' WHERE id = %s""",
            [self.tax_p_reav.id],
        )
        product = self.product_a.copy(
            {"name": "Old REAV product", "taxes_id": [(6, 0, self.tax_s_reav.ids)]}
        )
        kept_tax = self.env["account.chart.template"].ref(
            "account_tax_template_p_iva21_bi"
        )
        kept_tax.fiscal_position_ids -= self.fp_reav
        # In 18.0 the REAV taxes only replaced the 0 % (purchases), 4, 10 and
        # 21 % VAT, the migration of OpenUpgrade keeps only those
        reav_taxes = (self.tax_s_reav | self.tax_p_reav).with_context(active_test=False)
        original_taxes = {tax: tax.original_tax_ids for tax in reav_taxes}
        ChartTemplate = self.env["account.chart.template"]
        taxes_18 = self.env["account.tax"]
        for xmlid in (
            "s_iva4b",
            "s_iva4s",
            "s_iva10b",
            "s_iva10s",
            "s_iva21b",
            "s_iva21s",
            "p_iva0_bc",
            "p_iva4_bc",
            "p_iva4_sc",
            "p_iva10_bc",
            "p_iva10_sc",
            "p_iva21_bc",
            "p_iva21_sc",
        ):
            taxes_18 |= ChartTemplate.ref(f"account_tax_template_{xmlid}")
        for tax in reav_taxes:
            # The copies of the default taxes made by the test common keep
            # their replacements, they are not from the chart
            chart_taxes = tax.original_tax_ids.filtered(
                lambda original: original.get_external_id()[original.id]
            )
            tax.original_tax_ids -= chart_taxes - taxes_18
        product_nd = self._product_with_taxes("s_iva0b", "p_iva10_nd")
        self.env.flush_all()
        with self.assertLogs("odoo.addons.l10n_es_reav", "WARNING") as logs:
            self._run_migration()
        self.assertIn(product.display_name, logs.output[0])
        (self.tax_s_reav | self.tax_p_reav | kept_tax).invalidate_recordset()
        self.assertIn(self.fp_reav, kept_tax.fiscal_position_ids)
        self.assertEqual(self.tax_s_reav.l10n_es_regime_code, "05")
        self.assertEqual(self.tax_s_reav.l10n_es_applicability, "01")
        self.assertEqual(self.tax_p_reav.l10n_es_regime_code, "01")
        self.assertEqual(self.tax_p_reav.l10n_es_type, "no_deducible")
        reav_taxes.invalidate_recordset()
        for tax in reav_taxes:
            self.assertEqual(tax.original_tax_ids, original_taxes[tax])
        invoice = self.init_invoice(
            "out_invoice", partner=self.partner_a, products=product_nd
        )
        self.assertEqual(invoice.invoice_line_ids.tax_ids, self.tax_s_reav)
        bill = self.init_invoice(
            "in_invoice", partner=self.partner_a, products=product_nd
        )
        self.assertEqual(bill.invoice_line_ids.tax_ids, self.tax_p_reav)
