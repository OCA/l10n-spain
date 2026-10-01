# Copyright 2026 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo.tests import tagged

from odoo.addons.base.tests.common import BaseCommon


@tagged("post_install", "-at_install")
class TestL10nEsDigitalCanonWebsiteSale(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {"name": "Test Company", "currency_id": cls.env.ref("base.EUR").id}
        )
        cls.env["account.chart.template"]._load(
            template_code="es_pymes", company=cls.company, install_demo=False
        )
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=cls.company.ids)
        )
        cls.website = cls.env["website"].create(
            {"name": "Test Website", "company_id": cls.company.id}
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Phone 128GB",
                "l10n_es_digital_canon": "3_25.phone_128",
                "taxes_id": [(6, 0, cls.company.account_sale_tax_id.ids)],
            }
        )
        cls.canon_tax = cls.env.ref(
            f"account.{cls.company.id}_tax_template_canon_sale_3_25"
        )
        cls.order = cls.env["sale.order"].create(
            {
                "partner_id": cls.website.user_id.partner_id.id,
                "website_id": cls.website.id,
                "company_id": cls.company.id,
                "order_line": [(0, 0, {"product_id": cls.product.id})],
            }
        )

    def test_canon_in_website_cart_without_country(self):
        self.assertIn(self.canon_tax, self.order.order_line.tax_id)

    def test_canon_removed_with_foreign_delivery_address(self):
        self.order.partner_id = self.env["res.partner"].create(
            {"name": "French Customer", "country_id": self.env.ref("base.fr").id}
        )
        self.assertNotIn(self.canon_tax, self.order.order_line.tax_id)
