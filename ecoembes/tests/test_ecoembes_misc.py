# Copyright 2021-2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import exceptions
from odoo.tests.common import tagged, users

from .common import TestEcoembesBase


@tagged("post_install", "-at_install")
class TestEcoembesMisc(TestEcoembesBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ecoembes_market_type = cls.env["ecoembes.market.type"]
        cls.ecoembes_material_01 = cls.env.ref("ecoembes.ecoembes_material_01")
        cls.product = cls.env["product.product"].create(
            {"name": "Test Product", "default_code": "ECOEMBES"}
        )

    def test_ecoembes_market_type_name_get(self):
        items = self.ecoembes_market_type.name_search(name="C")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0][1], "Comercial")
        items = self.ecoembes_market_type.name_search(name="Industrial", operator="=")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0][1], "Industrial")

    def _test_ecoembes_model_misc(self, model):
        model_user = self.env[model]
        test_record = model_user.create({"name": "Test record", "reference": "1234"})
        self.assertEqual(test_record.reference, "1234")
        # Error
        with self.assertRaises(exceptions.ValidationError):
            model_user.create({"name": "Test record 2", "reference": "asasasas"})
        # Check name_search according to reference
        items = model_user.name_search(name="1234")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0][1], "Test record")
        items = model_user.name_search(name="Test record", operator="=")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0][1], "Test record")

    @users("user_system")
    def test_ecoembes_material_contrains_name_search(self):
        self._test_ecoembes_model_misc("ecoembes.material")

    @users("user_system")
    def test_ecoembes_packaging_constrains_name_search(self):
        self._test_ecoembes_model_misc("ecoembes.packaging")

    @users("user_system")
    def test_ecoembes_sector_constrains_name_search(self):
        self._test_ecoembes_model_misc("ecoembes.sector")

    @users("user_system")
    def test_ecoembes_submaterial_constrains_name_search(self):
        model_submaterial = self.env["ecoembes.submaterial"]
        test_record = model_submaterial.create(
            {
                "name": "Test record",
                "reference": "1234",
                "material_id": self.ecoembes_material_01.id,
            }
        )
        self.assertEqual(test_record.reference, "1234")
        # Error
        with self.assertRaises(exceptions.ValidationError):
            model_submaterial.create(
                {
                    "name": "Test material2",
                    "reference": "asasasas",
                    "material_id": self.ecoembes_material_01.id,
                }
            )

    @users("ecoembes_manager")
    def test_product_composition_create(self):
        record = self.env["product.composition"].create(
            {
                "product_id": self.product.id,
                "material_id": self.ecoembes_material_01.id,
                "submaterial_id": self.env.ref(
                    "ecoembes.ecoembes_submaterial_00_02"
                ).id,
                "packaging_id": self.env.ref("ecoembes.ecoembes_packaging_101").id,
                "market_type_id": self.env.ref("ecoembes.ecoembes_market_type_c").id,
            }
        )
        self.assertEqual(record.product_tmpl_id, self.product.product_tmpl_id)
        self.assertEqual(record.default_code, "ECOEMBES")
        self.assertEqual(self.product.composition_ids.ids, [record.id])
        product2 = (
            self.env["product.product"]
            .sudo()
            .create({"name": "Test Product2", "default_code": "ECOEMBES2"})
        )
        record.write({"product_id": product2.id})
        self.assertEqual(record.product_tmpl_id, product2.product_tmpl_id)
