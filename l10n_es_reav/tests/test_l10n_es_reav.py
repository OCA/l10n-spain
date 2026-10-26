# Copyright 2026 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo.tests import tagged

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
        agencies regime code."""
        for tax in self.tax_p_reav | self.tax_s_reav:
            self.assertEqual(tax.l10n_es_applicability, "01")
            self.assertEqual(tax.l10n_es_regime_code, "05")

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
