# Copyright 2013-2024 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import io
import zipfile

from odoo.tests import common


class TestL10nEsToponyms(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wizard = cls.env["config.es.toponyms"].create({"name": ""})

    def test_import(self):
        rows = [
            [
                "ES",
                "28801",
                "Alcala De Henares",
                "Madrid",
                "MD",
                "Madrid",
                "M",
                "",
                "",
                "40.4818",
                "-3.3635",
                "4",
            ],
            [
                "ES",
                "16150",
                "Vega Del Codorno",
                "Castilla-La Mancha",
                "CM",
                "Cuenca",
                "CU",
                "",
                "",
                "40.4333",
                "-1.9167",
                "4",
            ],
        ]
        tsv_content = "\n".join("\t".join(row) for row in rows) + "\n"
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("ES.txt", tsv_content)

        with common.MockHTTPClient(
            matcher=lambda req: "ES.zip" in req.url,
            return_body=zip_buffer.getvalue(),
        ):
            self.wizard.action_import_geonames()

        cities = self.env["res.city"].search(
            [("country_id", "=", self.env.ref("base.es").id)]
        )
        self.assertTrue(cities)
        self.assertTrue(cities.mapped("zip_ids"))
        city_names = set(cities.mapped("name"))
        self.assertIn("Alcala de Henares", city_names)
        self.assertIn("Vega del Codorno", city_names)
