# Copyright 2013-2024 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import requests

from odoo.tests import common


class TestL10nEsToponyms(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        cls._super_send = requests.Session.send
        super().setUpClass()
        cls.wizard = cls.env["config.es.toponyms"].create({"name": ""})

    @classmethod
    def _request_handler(cls, s, r, /, **kw):
        """Don't block external requests."""
        return cls._super_send(s, r, **kw)

    def test_import(self):
        self.wizard.with_context(max_import=10).execute()
        cities = self.env["res.city"].search(
            [("country_id", "=", self.env.ref("base.es").id)]
        )
        self.assertTrue(cities)
        self.assertTrue(cities.mapped("zip_ids"))
