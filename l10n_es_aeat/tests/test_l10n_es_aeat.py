# Copyright 2016-2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import SavepointCase


class TestL10nEsAeat(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.export_model = cls.env["l10n.es.aeat.report.export_to_boe"]
        cls.partner = cls.env["res.partner"].create({"name": "test partner"})

    def test_format_string(self):
        text = " &'(),-./01:;abAB_ÇÑ\"áéíóúÁÉÍÓÚ+!"
        self.assertEqual(
            self.export_model._format_string(text, len(text)),
            " &'(),-./01:;ABAB_ÇÑAEIOUAEIOU   ".encode("iso-8859-1"),
        )

    def test_parse_vat_info_es_wo_prefix(self):
        self.partner.vat = "12345678Z"
        self.partner.country_id = self.env.ref("base.es")
        country_code, identifier_type, vat_number = self.partner._parse_aeat_vat_info()
        self.assertEqual(country_code, "ES")
        self.assertEqual(identifier_type, "")
        self.assertEqual(vat_number, "12345678Z")

    def test_parse_vat_info_es_w_prefix(self):
        self.partner.vat = "ES12345678Z"
        country_code, identifier_type, vat_number = self.partner._parse_aeat_vat_info()
        self.assertEqual(country_code, "ES")
        self.assertEqual(identifier_type, "")
        self.assertEqual(vat_number, "12345678Z")

    def test_parse_vat_info_fr_wo_prefix(self):
        self.partner.vat = "61954506077"
        self.partner.country_id = self.env.ref("base.fr")
        country_code, identifier_type, vat_number = self.partner._parse_aeat_vat_info()
        self.assertEqual(country_code, "FR")
        self.assertEqual(identifier_type, "02")
        self.assertEqual(vat_number, "61954506077")

    def test_parse_vat_info_fr_w_prefix(self):
        self.partner.vat = "fr61954506077"
        country_code, identifier_type, vat_number = self.partner._parse_aeat_vat_info()
        self.assertEqual(country_code, "FR")
        self.assertEqual(identifier_type, "02")
        self.assertEqual(vat_number, "61954506077")

    def test_parse_vat_info_gf_wo_prefix(self):
        self.partner.vat = "61954506077"
        self.partner.country_id = self.env.ref("base.gf")
        country_code, identifier_type, vat_number = self.partner._parse_aeat_vat_info()
        self.assertEqual(country_code, "FR")
        self.assertEqual(identifier_type, "02")
        self.assertEqual(vat_number, "61954506077")

    def test_parse_vat_info_gf_w_prefix(self):
        self.partner.vat = "GF61954506077"
        country_code, identifier_type, vat_number = self.partner._parse_aeat_vat_info()
        self.assertEqual(country_code, "FR")
        self.assertEqual(identifier_type, "02")
        self.assertEqual(vat_number, "61954506077")

    def test_parse_vat_info_cu_wo_prefix(self):
        self.partner.vat = "12345678Z"
        self.partner.country_id = self.env.ref("base.cu")
        country_code, identifier_type, vat_number = self.partner._parse_aeat_vat_info()
        self.assertEqual(country_code, "CU")
        self.assertEqual(identifier_type, "04")
        self.assertEqual(vat_number, "12345678Z")

    def test_parse_vat_info_cu_w_prefix(self):
        self.partner.vat = "CU12345678Z"
        country_code, identifier_type, vat_number = self.partner._parse_aeat_vat_info()
        self.assertEqual(country_code, "")
        self.assertEqual(identifier_type, "04")
        self.assertEqual(vat_number, "CU12345678Z")
