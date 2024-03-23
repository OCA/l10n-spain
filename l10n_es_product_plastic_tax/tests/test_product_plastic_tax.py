# © 2022 FactorLibre - Luis J. Salvatierra <luis.salvatierra@factorlibre.com>
# © 2023 FactorLibre - Aritz Olea <aritz.olea@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestProductPlasticTax(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.user = cls.env.user
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.prod_att_1 = cls.env["product.attribute"].create({"name": "Color"})
        cls.prod_attr1_v1 = cls.env["product.attribute.value"].create(
            {"name": "red", "attribute_id": cls.prod_att_1.id}
        )
        cls.prod_attr1_v2 = cls.env["product.attribute.value"].create(
            {"name": "blue", "attribute_id": cls.prod_att_1.id}
        )
        cls.size_attr = cls.env["product.attribute"].create({"name": "Size"})
        cls.size_attr_value_s = cls.env["product.attribute.value"].create(
            {"name": "S", "attribute_id": cls.size_attr.id}
        )
        cls.size_attr_value_m = cls.env["product.attribute.value"].create(
            {"name": "M", "attribute_id": cls.size_attr.id}
        )
        cls.size_attr_value_l = cls.env["product.attribute.value"].create(
            {"name": "L", "attribute_id": cls.size_attr.id}
        )

    def test_01_product_template_with_plastic_tax(self):
        plastic_tax_product_code = "A"
        total_plastic_weight = 0.1
        non_reusable_plastic_weight = 0.1
        product_template = self.env["product.template"].create(
            {
                "name": "T-shirt with plastic",
                "uom_id": self.uom_unit.id,
                "uom_po_id": self.uom_unit.id,
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": self.prod_att_1.id,
                            "value_ids": [
                                (6, 0, [self.prod_attr1_v1.id, self.prod_attr1_v2.id])
                            ],
                        },
                    )
                ],
                "plastic_tax_product_code": plastic_tax_product_code,
                "total_plastic_weight": total_plastic_weight,
                "non_reusable_plastic_weight": non_reusable_plastic_weight,
            }
        )
        self.assertEqual(2, len(product_template.product_variant_ids))
        self.assertTrue(
            all(
                v.plastic_tax_product_code == plastic_tax_product_code
                for v in product_template.product_variant_ids
            )
        )
        self.assertTrue(
            all(
                v.total_plastic_weight == total_plastic_weight
                for v in product_template.product_variant_ids
            )
        )
        self.assertTrue(
            all(
                v.non_reusable_plastic_weight == non_reusable_plastic_weight
                for v in product_template.product_variant_ids
            )
        )
        # If you modify the template, propagate changes to all its variants
        # but not the other way around
        variant = product_template.product_variant_ids[0]
        variant.plastic_tax_product_code = "C"
        variant.total_plastic_weight = total_plastic_weight + 0.1
        variant.non_reusable_plastic_weight = total_plastic_weight + 0.1
        self.assertEqual(
            plastic_tax_product_code, product_template.plastic_tax_product_code
        )
        self.assertNotEqual(plastic_tax_product_code, variant.plastic_tax_product_code)
        self.assertEqual(total_plastic_weight, product_template.total_plastic_weight)
        self.assertNotEqual(total_plastic_weight, variant.total_plastic_weight)
        self.assertEqual(
            non_reusable_plastic_weight, product_template.non_reusable_plastic_weight
        )
        self.assertNotEqual(
            non_reusable_plastic_weight, variant.non_reusable_plastic_weight
        )
        # Reset template configuration
        product_template.plastic_tax_product_code = plastic_tax_product_code
        product_template.non_reusable_plastic_weight = non_reusable_plastic_weight
        product_template.total_plastic_weight = total_plastic_weight
        self.assertEqual(
            plastic_tax_product_code, product_template.plastic_tax_product_code
        )
        self.assertEqual(plastic_tax_product_code, variant.plastic_tax_product_code)
        self.assertEqual(total_plastic_weight, product_template.total_plastic_weight)
        self.assertEqual(total_plastic_weight, variant.total_plastic_weight)
        self.assertEqual(
            non_reusable_plastic_weight, product_template.non_reusable_plastic_weight
        )
        self.assertEqual(
            non_reusable_plastic_weight, variant.non_reusable_plastic_weight
        )

    def test_02_product_template_without_plastic_tax(self):
        product_template = self.env["product.template"].create(
            {
                "name": "T-shirt without plastic",
                "uom_id": self.uom_unit.id,
                "uom_po_id": self.uom_unit.id,
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": self.prod_att_1.id,
                            "value_ids": [
                                (6, 0, [self.prod_attr1_v1.id, self.prod_attr1_v2.id])
                            ],
                        },
                    )
                ],
            }
        )
        self.assertEqual(2, len(product_template.product_variant_ids))
        self.assertTrue(
            all(
                not v.plastic_tax_product_code
                for v in product_template.product_variant_ids
            )
        )
        self.assertTrue(
            all(
                v.total_plastic_weight == 0.0
                for v in product_template.product_variant_ids
            )
        )
        self.assertTrue(
            all(
                v.non_reusable_plastic_weight == 0.0
                for v in product_template.product_variant_ids
            )
        )

    def test_03_create_variants(self):
        plastic_tax_product_code = "A"
        product_template = self.env["product.template"].create(
            {
                "name": "T-shirt with plastic",
                "uom_id": self.uom_unit.id,
                "uom_po_id": self.uom_unit.id,
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": self.prod_att_1.id,
                            "value_ids": [
                                (6, 0, [self.prod_attr1_v1.id, self.prod_attr1_v2.id])
                            ],
                        },
                    )
                ],
                "plastic_tax_product_code": plastic_tax_product_code,
                "total_plastic_weight": 0.1,
                "non_reusable_plastic_weight": 0.1,
            }
        )
        self.assertEqual(2, len(product_template.product_variant_ids))
        product_template.attribute_line_ids = [
            (
                0,
                0,
                {
                    "attribute_id": self.size_attr.id,
                    "value_ids": [
                        (
                            6,
                            0,
                            [
                                self.size_attr_value_s.id,
                                self.size_attr_value_m.id,
                                self.size_attr_value_l.id,
                            ],
                        )
                    ],
                },
            )
        ]
        self.assertEqual(6, len(product_template.product_variant_ids))
        self.assertTrue(
            all(
                v.plastic_tax_product_code == plastic_tax_product_code
                for v in product_template.product_variant_ids
            )
        )
        self.assertTrue(
            all(
                v.total_plastic_weight == 0.1
                for v in product_template.product_variant_ids
            )
        )
        self.assertTrue(
            all(
                v.non_reusable_plastic_weight == 0.1
                for v in product_template.product_variant_ids
            )
        )

    def test_04_create_product_product(self):
        plastic_tax_product_code = "B"
        total_plastic_weight = 0.1
        non_reusable_plastic_weight = 0.1
        product = self.env["product.product"].create(
            {
                "name": "T-shirt with plastic - White",
                "uom_id": self.uom_unit.id,
                "uom_po_id": self.uom_unit.id,
                "plastic_tax_product_code": plastic_tax_product_code,
                "total_plastic_weight": total_plastic_weight,
                "non_reusable_plastic_weight": non_reusable_plastic_weight,
            }
        )
        template = product.product_tmpl_id
        self.assertEqual(product.plastic_tax_product_code, plastic_tax_product_code)
        self.assertEqual(template.plastic_tax_product_code, plastic_tax_product_code)
        self.assertEqual(product.total_plastic_weight, total_plastic_weight)
        self.assertEqual(template.total_plastic_weight, total_plastic_weight)
        self.assertEqual(
            product.non_reusable_plastic_weight, non_reusable_plastic_weight
        )
        self.assertEqual(
            template.non_reusable_plastic_weight, non_reusable_plastic_weight
        )

    def test_05_modify_existing_variant_with_plastic_tax(self):
        product_template = self.env["product.template"].create(
            {
                "name": "T-shirt with plastic tax variant",
                "uom_id": self.uom_unit.id,
                "uom_po_id": self.uom_unit.id,
            }
        )
        self.assertEqual(1, len(product_template.product_variant_ids))
        self.assertTrue(
            all(
                not v.plastic_tax_product_code
                for v in product_template.product_variant_ids
            )
        )
        self.assertTrue(
            all(
                v.total_plastic_weight == 0.0
                for v in product_template.product_variant_ids
            )
        )
        self.assertTrue(
            all(
                v.non_reusable_plastic_weight == 0.0
                for v in product_template.product_variant_ids
            )
        )
        plastic_tax_product_code = "B"
        total_plastic_weight = 0.1
        non_reusable_plastic_weight = 0.1
        product = product_template.product_variant_ids
        product.write(
            {
                "plastic_tax_product_code": plastic_tax_product_code,
                "total_plastic_weight": total_plastic_weight,
                "non_reusable_plastic_weight": non_reusable_plastic_weight,
            }
        )
        self.assertEqual(product.plastic_tax_product_code, plastic_tax_product_code)
        self.assertEqual(
            product_template.plastic_tax_product_code, plastic_tax_product_code
        )
        self.assertEqual(product.total_plastic_weight, total_plastic_weight)
        self.assertEqual(product_template.total_plastic_weight, total_plastic_weight)
        self.assertEqual(
            product.non_reusable_plastic_weight, non_reusable_plastic_weight
        )
        self.assertEqual(
            product_template.non_reusable_plastic_weight, non_reusable_plastic_weight
        )
