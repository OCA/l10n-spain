# Copyright 2026 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestL10nEsShoppingfeedIntegration(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sf_store = cls.env["shoppingfeed.store"].create(
            {
                "name": "Test SF Store",
                "username": "test_user",
                "password": "test_pass",
                "company_id": cls.env.company.id,
            }
        )

    def test_invalid_billing_vat_goes_to_aeat_identification(self):
        partner = self.env["sale.order"]._shoppingfeed_prepare_partner(
            {
                "firstName": "John",
                "lastName": "Invalid",
                "email": "john.invalid@example.com",
                "country": "ES",
            },
            self.sf_store,
            additional_fields={"buyer_tax_registration_id": "12345678A"},
        )
        self.assertFalse(partner.vat)
        self.assertEqual(partner.aeat_identification, "12345678A")
        self.assertEqual(partner.aeat_identification_type, "06")
        self.assertIn("12345678A", partner.comment)

    def test_billing_partner_dedup_by_aeat_identification(self):
        SO = self.env["sale.order"]
        billing = {
            "firstName": "John",
            "lastName": "Invalid",
            "email": "john.invalid@example.com",
            "country": "ES",
        }
        additional_fields = {"buyer_tax_registration_id": "12345678A"}
        partner = SO._shoppingfeed_prepare_partner(
            billing, self.sf_store, additional_fields=additional_fields
        )
        same_partner = SO._shoppingfeed_prepare_partner(
            billing, self.sf_store, additional_fields=additional_fields
        )
        self.assertEqual(partner, same_partner)
