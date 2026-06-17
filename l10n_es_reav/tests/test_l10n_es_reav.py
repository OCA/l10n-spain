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

    def test_reav_on_vendor_bill(self):
        bill = self.init_invoice(
            "in_invoice", partner=self.partner_a, products=self.product_a
        )
        self.assertEqual(bill.fiscal_position_id, self.fp_reav)
        self.assertEqual(bill.invoice_line_ids.tax_ids, self.tax_p_reav)
