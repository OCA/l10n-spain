# Copyright 2026 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.addons.base.tests.common import BaseCommon


class TestWebsiteSaleInsuranceCaser(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.category = cls.env["product.category"].create(
            {"name": "Phones", "caser_asset_type": "200021"}
        )
        cls.brand_with_code = cls.env["product.brand"].create(
            {"name": "SAMSUNG", "caser_mobile_code": "479"}
        )
        cls.brand_without_code = cls.env["product.brand"].create({"name": "NONAME"})

    def _create_product(self, brand):
        return self.env["product.template"].create(
            {
                "name": "Phone",
                "categ_id": self.category.id,
                "product_brand_id": brand.id,
            }
        )

    def test_insurable_only_when_brand_has_caser_code(self):
        product = self._create_product(self.brand_with_code)
        self.assertTrue(product.caser_insurance_ecommerce)

    def test_not_insurable_when_brand_has_no_caser_code(self):
        product = self._create_product(self.brand_without_code)
        self.assertFalse(product.caser_insurance_ecommerce)

    def test_not_insurable_recomputes_when_brand_code_filled(self):
        product = self._create_product(self.brand_without_code)
        self.assertFalse(product.caser_insurance_ecommerce)
        self.brand_without_code.caser_mobile_code = "999"
        self.assertTrue(product.caser_insurance_ecommerce)
