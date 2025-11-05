# Copyright 2016-2017 Tecnativa - Pedro M. Baeza
# Copyright 2017 Tecnativa - Carlos Dauden <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3).

import requests

from odoo.tests import common


class TestL10nEsPartner(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        cls._super_send = requests.Session.send
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

    @classmethod
    def _request_handler(cls, s, r, /, **kw):
        """Don't block external requests."""
        return cls._super_send(s, r, **kw)

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
                "street": "My street",
            }
        )
        self.assertEqual(partner2.display_name, "Nombre comercial (Empresa de prueba)")
        self.assertEqual(partner2.complete_name, "Empresa de prueba")
        self.assertEqual(
            partner2.with_context(show_address=True).display_name,
            "Nombre comercial (Empresa de prueba)\nMy street",
        )
        # We will enforce the computation, but nothing should change
        partner2.with_context(
            show_address=True, display_commercial=True
        )._compute_complete_name()
        self.assertEqual(partner2.complete_name, "Empresa de prueba")
        partner2.write({"comercial": "Nuevo nombre"})
        self.assertEqual(partner2.display_name, "Nuevo nombre (Empresa de prueba)")
        names = dict(
            [
                (
                    partner2.id,
                    partner2.with_context(no_display_commercial=True).display_name,
                )
            ]
        )
        self.assertEqual(names.get(partner2.id), "Empresa de prueba")
        names = dict([(partner2.id, partner2.display_name)])
        self.assertEqual(names.get(partner2.id), "Nuevo nombre (Empresa de prueba)")
