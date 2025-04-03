# Copyright 2016-2017 Tecnativa - Pedro M. Baeza
# Copyright 2017 Tecnativa - Carlos Dauden <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3).

from odoo.tests import common


class TestL10nEsPartner(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Make sure there's no commercial name on display_name field
        cls.env["ir.config_parameter"].set_param("l10n_es_partner.name_pattern", "")
        cls.country_spain = cls.env.ref("base.es")
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Empresa de prueba",
                "comercial": "Nombre comercial",
                "vat": "ES12345678Z",
                "country_id": cls.country_spain.id,
            }
        )
        cls.wizard = cls.env["l10n.es.partner.import.wizard"].create({})
        cls.env.user.company_id.country_id = cls.country_spain.id
        cls.bank_obj = cls.env["res.partner.bank"].with_context(
            default_partner_id=cls.partner.id
        )

    def test_search_commercial(self):
        partner_obj = self.env["res.partner"]
        self.assertIn(
            self.partner.id, map(lambda x: x[0], partner_obj.name_search("prueba"))
        )
        self.assertNotIn(
            self.partner.id,
            map(
                lambda x: x[0], partner_obj.name_search("prueba", operator="not ilike")
            ),
        )
        self.assertIn(
            self.partner.id, map(lambda x: x[0], partner_obj.name_search("comercial"))
        )
        self.assertNotIn(
            self.partner.id,
            map(
                lambda x: x[0],
                partner_obj.name_search("comercial", operator="not ilike"),
            ),
        )

    def test_import_banks(self):
        # Then import banks
        self.wizard.import_local()
        bank = self.env["res.bank"].search([("code", "=", "0182")])
        self.assertTrue(bank)
        # Make sure the bank doesn't exist
        bank.unlink()
        # Import banks again but now from Internet
        self.wizard.execute()
        bank = self.env["res.bank"].search([("code", "=", "0182")])
        self.assertTrue(bank)

    def test_name(self):
        self.env["ir.config_parameter"].set_param(
            "l10n_es_partner.name_pattern", "%(comercial_name)s (%(name)s)"
        )
        partner2 = self.env["res.partner"].create(
            {
                "name": "Empresa de prueba",
                "comercial": "Nombre comercial",
                "street": "Calle Mayor, 1",
                "zip": "50001",
                "city": "Zaragoza",
                "state_id": self.env.ref("base.state_es_z").id,
                "country_id": self.country_spain.id,
            }
        )
        self.assertEqual(partner2.display_name, "Nombre comercial (Empresa de prueba)")
        partner2.write({"comercial": "Nuevo nombre"})
        self.assertEqual(partner2.display_name, "Nuevo nombre (Empresa de prueba)")
        names = dict(partner2.with_context(no_display_commercial=True).name_get())
        self.assertEqual(names.get(partner2.id), "Empresa de prueba")
        names = dict(partner2.name_get())
        self.assertEqual(names.get(partner2.id), "Nuevo nombre (Empresa de prueba)")
        names = dict(partner2.with_context(show_address=True).name_get())
        self.assertEqual(
            names.get(partner2.id),
            "Nuevo nombre (Empresa de prueba)\n"
            "Calle Mayor, 1\n"
            "50001 Zaragoza (Zaragoza)\n"
            "Spain",
        )
        names = dict(
            partner2.with_context(show_address=True, address_inline=True).name_get()
        )
        self.assertEqual(
            names.get(partner2.id),
            "Nuevo nombre (Empresa de prueba), Calle Mayor, 1, "
            "50001 Zaragoza (Zaragoza), Spain",
        )
        names = dict(
            partner2.with_context(show_address=True, html_format=True).name_get()
        )
        self.assertEqual(
            names.get(partner2.id),
            "Nuevo nombre (Empresa de prueba)<br/>"
            "Calle Mayor, 1<br/>"
            "50001 Zaragoza (Zaragoza)<br/>"
            "Spain",
        )
