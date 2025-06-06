# Copyright 2025 Netkia - Carlos Sainz-Pardo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from odoo.tests import common


class TestL10nEsAeatRealEstate(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "vat": "ES12345678Z",
            }
        )
        self.state = self.env["res.country.state"].create(
            {
                "name": "Madrid",
                "code": "28",
                "country_id": self.env.ref("base.es").id,
            }
        )
        self.city = self.env["res.city"].create(
            {
                "name": "Madrid",
                "state_id": self.state.id,
                "country_id": self.env.ref("base.es").id,
            }
        )
        self.zip_id = self.env["res.city.zip"].create(
            {
                "name": "28013",
                "city_id": self.city.id,
                "state_id": self.state.id,
                "country_id": self.env.ref("base.es").id,
            }
        )

    def test_create_real_estate(self):
        real_estate = self.env["l10n.es.aeat.real_estate"].create(
            {
                "name": "Test Property",
                "partner_id": self.partner.id,
                "address": "Gran Via",
                "number_type": "NUM",
                "zip_id": self.zip_id.id,
                "zip": "28013",
                "city": "Madrid",
                "state_id": self.state.id,
            }
        )

        # Validaciones
        self.assertEqual(real_estate.representative_vat, self.partner.vat)
        self.assertEqual(real_estate.state_code, "28")
        self.assertTrue(real_estate.check_ok)
        self.assertFalse(real_estate.error_text)
