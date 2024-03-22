# Copyright 2016-2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import exceptions
from odoo.tests.common import TransactionCase


class TestL10nEsAeat(TransactionCase):
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
        self.partner.write(
            {"vat": "12345678Z", "country_id": self.env.ref("base.es").id}
        )
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

    def test_parse_vat_info_es_passport_exception(self):
        with self.assertRaises(exceptions.ValidationError):
            self.partner.write(
                {"vat": "ZZ_MY_PASSPORT", "country_id": self.env.ref("base.es").id}
            )

    def test_parse_vat_info_es_passport(self):
        self.partner.write(
            {
                "aeat_identification": "ZZ_MY_PASSPORT",
                "aeat_identification_type": "05",
                "country_id": self.env.ref("base.es").id,
            }
        )
        country_code, identifier_type, identifier = self.partner._parse_aeat_vat_info()
        self.assertEqual(country_code, "ES")
        self.assertEqual(identifier_type, "05")
        self.assertEqual(identifier, "ZZ_MY_PASSPORT")

    def test_parse_vat_info_fr_wo_prefix(self):
        self.partner.write(
            {"vat": "61954506077", "country_id": self.env.ref("base.fr").id}
        )
        country_code, identifier_type, vat_number = self.partner._parse_aeat_vat_info()
        self.assertEqual(country_code, "FR")
        self.assertEqual(vat_number, "61954506077")

    def test_parse_vat_info_fr_w_prefix(self):
        self.partner.vat = "fr61954506077"
        country_code, identifier_type, vat_number = self.partner._parse_aeat_vat_info()
        self.assertEqual(country_code, "FR")
        self.assertEqual(identifier_type, "02")
        self.assertEqual(vat_number, "61954506077")

    def test_parse_vat_info_gf_wo_prefix(self):
        self.partner.write(
            {"vat": "61954506077", "country_id": self.env.ref("base.gf").id}
        )
        country_code, identifier_type, vat_number = self.partner._parse_aeat_vat_info()
        self.assertEqual(country_code, "FR")
        self.assertEqual(identifier_type, "04")
        self.assertEqual(vat_number, "61954506077")

    def test_parse_vat_info_gf_w_prefix(self):
        self.partner.vat = "GF61954506077"
        country_code, identifier_type, vat_number = self.partner._parse_aeat_vat_info()
        self.assertEqual(country_code, "FR")
        self.assertEqual(identifier_type, "04")
        self.assertEqual(vat_number, "GF61954506077")

    def test_parse_vat_info_cu_wo_prefix(self):
        self.partner.write(
            {"vat": "12345678Z", "country_id": self.env.ref("base.cu").id}
        )
        country_code, identifier_type, vat_number = self.partner._parse_aeat_vat_info()
        self.assertEqual(country_code, "CU")
        self.assertEqual(identifier_type, "04")
        self.assertEqual(vat_number, "12345678Z")

    def test_parse_vat_info_cu_w_prefix(self):
        self.partner.vat = "CU12345678Z"
        country_code, identifier_type, vat_number = self.partner._parse_aeat_vat_info()
        self.assertEqual(country_code, "CU")
        self.assertEqual(identifier_type, "04")
        self.assertEqual(vat_number, "CU12345678Z")

    def test_unique_date_range(self):
        self.env["l10n.es.aeat.map.tax"].create(
            {"date_from": "2020-01-01", "model": 303}
        )
        with self.assertRaises(exceptions.UserError):
            self.env["l10n.es.aeat.map.tax"].create(
                {"date_to": "2021-01-01", "model": 303}
            )

    def test_map_aeat_iso_code_greece(self):
        res_partner_obj = self.env["res.partner"]
        greece_country = self.env.ref("base.gr")
        iso_code = "EL"
        mapping_return = res_partner_obj._map_aeat_country_iso_code(greece_country)
        self.assertEqual(iso_code, mapping_return)

    def test_map_aeat_iso_code_no_mapping(self):
        res_partner_obj = self.env["res.partner"]
        spain_country = self.env.ref("base.es")
        iso_code = "ES"
        mapping_return = res_partner_obj._map_aeat_country_iso_code(spain_country)
        self.assertEqual(iso_code, mapping_return)
