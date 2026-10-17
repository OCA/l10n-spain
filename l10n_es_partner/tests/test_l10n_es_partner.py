# Copyright 2016-2017 Tecnativa - Pedro M. Baeza
# Copyright 2017 Tecnativa - Carlos Dauden <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3).

from odoo.tests import Form, common


class TestL10nEsPartner(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Make sure there's no commercial name on display_name field
        cls.env["ir.config_parameter"].set_str("l10n_es_partner.name_pattern", "")
        cls.country_spain = cls.env.ref("base.es")
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Empresa de prueba",
                "comercial": "Nombre comercial",
                "vat": "ES12345678Z",
                "country_id": cls.country_spain.id,
            }
        )

    def test_search_commercial(self):
        partner_obj = self.env["res.partner"]
        self.assertIn(
            self.partner.id, [x[0] for x in partner_obj.name_search("prueba")]
        )
        self.assertNotIn(
            self.partner.id,
            [x[0] for x in partner_obj.name_search("prueba", operator="not ilike")],
        )
        self.assertIn(
            self.partner.id, [x[0] for x in partner_obj.name_search("comercial")]
        )
        self.assertNotIn(
            self.partner.id,
            [x[0] for x in partner_obj.name_search("comercial", operator="not ilike")],
        )

    def test_search_view_commercial(self):
        """The name filter of the contacts search view finds the trade name"""
        partner_obj = self.env["res.partner"]
        self.assertIn(
            self.partner, partner_obj.search([("display_name", "ilike", "comercial")])
        )
        self.assertNotIn(
            self.partner,
            partner_obj.search([("display_name", "not ilike", "comercial")]),
        )

    def test_name(self):
        self.env["ir.config_parameter"].set_str(
            "l10n_es_partner.name_pattern", "%(comercial_name)s (%(name)s)"
        )
        partner2 = self.env["res.partner"].create(
            {
                "name": "Empresa de prueba",
                "comercial": "Nombre comercial",
                "street": "My street",
            }
        )
        self.assertEqual(partner2.display_name, "Nombre comercial (Empresa de prueba)")
        self.assertEqual(partner2.complete_name, "Nombre comercial (Empresa de prueba)")
        self.assertEqual(
            partner2.with_context(show_address=True).display_name,
            "Nombre comercial (Empresa de prueba)\nMy street",
        )
        # We will enforce the computation
        partner2.with_context(
            show_address=True, display_commercial=True
        )._compute_complete_name()
        partner2.write({"comercial": "Nuevo nombre"})
        self.assertEqual(partner2.display_name, "Nuevo nombre (Empresa de prueba)")
        self.assertEqual(partner2.complete_name, "Nuevo nombre (Empresa de prueba)")
        names = {
            partner2.id: partner2.with_context(no_display_commercial=True).display_name
        }
        self.assertEqual(names.get(partner2.id), "Empresa de prueba")
        names = {partner2.id: partner2.display_name}
        self.assertEqual(names.get(partner2.id), "Nuevo nombre (Empresa de prueba)")

    def test_form_commercial_visibility(self):
        """The trade name is editable on contacts without parent, even
        without VAT (so not companies in 20.0), but not on child contacts"""
        with Form(self.env["res.partner"]) as partner_form:
            partner_form.name = "Autónomo sin NIF"
            partner_form.comercial = "Bar Pepe"
        self.assertFalse(partner_form.record.is_company)
        self.assertEqual(partner_form.record.comercial, "Bar Pepe")
        child_form = Form(self.env["res.partner"])
        child_form.name = "Contacto"
        child_form.parent_id = self.partner
        with self.assertRaises(AssertionError):
            child_form.comercial = "Otro nombre"
