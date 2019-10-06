# Copyright 2013-2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import common


class TestL10nEsToponyms(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestL10nEsToponyms, cls).setUpClass()
        cls.wizard = cls.env["config.es.toponyms"].create({"name": ""})

    def test_import(self):
        self.wizard.with_context(max_import=10).execute()
        cities = self.env["res.city"].search(
            [("country_id", "=", self.env.ref("base.es").id)]
        )
        self.assertTrue(cities)
        self.assertTrue(cities.mapped("zip_ids"))
