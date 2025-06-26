# Copyright 2024 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3).
import csv
import io

from odoo.tests.common import TransactionCase
from odoo.tools import file_open

TEST_CODES = [
    "10.21",
    "10.22",
    "10.43",
    "10.44",
    "10.53",
    "35.15",
    "35.16",
    "35.17",
    "35.18",
    "35.19",
    "41.21",
    "41.22",
    "59.15",
    "59.16",
    "59.17",
    "59.18",
    "85.43",
    "85.44",
    "87.31",
    "87.32",
    "88.11",
    "88.12",
    "91.05",
    "91.06",
]


class TestL10nCaEsCnae(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["res.lang"]._activate_lang("ca_ES")

    def test_create_catalan_translation_industries(self):
        wizard = self.env["res.partner.industry.eu.nace.wizard"].create({})
        wizard.create_spanish_industries()
        wizard.spanish_industries_into_catalan()
        with file_open(
            "l10n_ca_es_cnae/data/res.partner.industry.cat.csv", "rb"
        ) as csvfile:
            text_stream = io.TextIOWrapper(csvfile, encoding="utf-8")
            reader = csv.reader(text_stream, delimiter=",", quotechar='"')
            all_naces = self.env["res.partner.industry"].search_read(
                [("full_name", "like", " - ")], ["full_name"]
            )
            nace_map = {
                nace.get("full_name").split(" - ")[0]: nace.get("id")
                for nace in all_naces
            }
            for row in reader:
                if row[0] in TEST_CODES:
                    nace = self.env["res.partner.industry"].browse(nace_map[row[0]])
                    self.assertEqual(nace.with_context(lang="ca_ES").name, row[1])
