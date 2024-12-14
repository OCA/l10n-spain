from odoo.tests import common


class TestAeatPartner(common.TransactionCase):
    def setUp(self):
        super().setUp()

        self.company = self.env["res.company"].create({
            "name": "Test Company",
        })

        self.partner = self.env["res.partner"].create({
            "name": "Test Partner",
            "vat": "ES12345678Z",
            "country_id": self.env.ref("base.es").id,
        })

    def test_compute_aeat_sending_enabled(self):
        record_partner = self.partner.create({
            "name": "Test Mixin Record",
            "company_id": self.company.id,
        })

        self.assertFalse(
            record_partner.aeat_sending_enabled,
            "Field aeat_sending_enabled should be False."
        )

    def test_parse_aeat_vat_info(self):
        self.partner.write({
           "vat": "ES12345678Z",
           "country_id": self.env.ref("base.es").id,
        })
        country_code, identifier_type, vat_number = self.partner._parse_aeat_vat_info()
        self.assertEqual(country_code, "ES", "Code should be 'ES'")
        self.assertEqual(identifier_type, "", "ID type should be empty for ES")
        self.assertEqual(vat_number, "12345678Z", "VAT should be'12345678Z'")

        self.partner.write({
            "vat": "US12345678Z",
            "country_id": self.env.ref("base.us").id,
        })
        country_code, identifier_type, vat_number = self.partner._parse_aeat_vat_info()
        self.assertEqual(country_code, "US", "Code should be 'US'")
        self.assertEqual(identifier_type, "04", "ID type should be '04'")
        self.assertEqual(vat_number, "US12345678Z", "VAT should be '12345678Z'")

        self.partner.write({
            "vat": False,
            "country_id": self.env.ref("base.de").id,
        })
        country_code, identifier_type, vat_number = self.partner._parse_aeat_vat_info()
        self.assertEqual(country_code, "DE", "Code should be 'DE'")
        self.assertEqual(identifier_type, "02", "ID type should be '02'")
        self.assertEqual(vat_number, "", "VAT should be empty")

        self.partner.write({
            "vat": False,
            "country_id": False,
        })
        country_code, identifier_type, vat_number = self.partner._parse_aeat_vat_info()
        self.assertEqual(country_code, "", "Code should be empty")
        self.assertEqual(identifier_type, "04", "ID type should be '04'")
        self.assertEqual(vat_number, "", "VAT should be empty")
