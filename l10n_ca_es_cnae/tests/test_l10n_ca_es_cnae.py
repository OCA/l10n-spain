# Copyright 2024 Manuel Regidor <manuel.regidor@sygel.es>
# Copyright 2026 Moduon Team S.L. <info@moduon.team>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3).
import csv
import io

from odoo.tests.common import TransactionCase
from odoo.tools import file_open

# CNAE 2025 subclasses that keep the code and activity they had in CNAE 2009
TEST_CODES = [
    "10.21",
    "10.22",
    "10.43",
    "10.44",
    "10.53",
    "10.54",
    "59.15",
    "87.31",
    "87.32",
    "88.11",
    "88.12",
]


class TestL10nCaEsCnae(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["res.lang"]._activate_lang("ca_ES")
        cls.wizard = cls.env["res.partner.industry.eu.nace.wizard"].create({})
        with file_open(
            "l10n_ca_es_cnae/data/res.partner.industry.cat.csv", "rb"
        ) as csvfile:
            text_stream = io.TextIOWrapper(csvfile, encoding="utf-8")
            cls.catalan = dict(csv.reader(text_stream, delimiter=",", quotechar='"'))

    def test_create_catalan_translation_industries(self):
        self.wizard.create_spanish_industries()
        self.wizard.spanish_industries_into_catalan()
        nace_map = self.env["res.partner.industry"]._get_nace_map("cnae2025")
        for code in TEST_CODES:
            nace = self.env["res.partner.industry"].browse(nace_map[code])
            self.assertEqual(nace.with_context(lang="ca_ES").name, self.catalan[code])

    def test_skip_codes_with_another_activity(self):
        """47.81 was market stalls in CNAE 2009 and is motor vehicles in 2025."""
        industry = self.env["res.partner.industry"]
        motor = industry.browse(industry._get_nace_map()["47.81"])
        name = motor.name
        self.wizard.spanish_industries_into_catalan()
        self.assertEqual(motor.with_context(lang="ca_ES").name, name)
        self.assertNotEqual(self.catalan["47.81"], name)
