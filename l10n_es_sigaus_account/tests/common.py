# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestL10nEsSigausCommon(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("base.main_company")
        cls.company.write({"sigaus_enable": True, "sigaus_date_from": "2022-01-01"})
        cls.partner = cls.env["res.partner"].create({"name": "Test"})
        cls.fiscal_position_sigaus = cls.env["account.fiscal.position"].create(
            {"name": "Test Fiscal Sigaus", "active": True, "sigaus_subject": True}
        )
        cls.fiscal_position_no_sigaus = cls.env["account.fiscal.position"].create(
            {"name": "Test Fiscal Sigaus", "active": True, "sigaus_subject": False}
        )
        cls.category_sigaus = cls.env["product.category"].create(
            {"name": "Sigaus Category", "sigaus_subject": True}
        )
        cls.product_sigaus_no = cls.env["product.product"].create(
            {
                "name": "Product-1",
                "sigaus_subject": "no",
                "weight": 1,
            }
        )
        cls.product_sigaus_in_product = cls.env["product.product"].create(
            {
                "name": "Product (SIGAUS in product)",
                "sigaus_subject": "yes",
                "weight": 1,
            }
        )
        cls.product_sigaus_in_category = cls.env["product.product"].create(
            {
                "name": "Product (SIGAUS in category)",
                "sigaus_subject": "category",
                "weight": 2,
                "categ_id": cls.category_sigaus.id,
            }
        )
        cls.product_sigaus_in_category_excluded = cls.env["product.product"].create(
            {
                "name": "Product (SIGAUS in category excluded)",
                "sigaus_subject": "no",
                "weight": 3,
                "categ_id": cls.category_sigaus.id,
            }
        )
        cls.product_sigaus_no_weight = cls.env["product.product"].create(
            {
                "name": "Product (SIGAUS no weight)",
                "sigaus_subject": "yes",
                "weight": 0,
            }
        )
