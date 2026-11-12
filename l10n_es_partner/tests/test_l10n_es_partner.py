# Copyright 2016-2017 Tecnativa - Pedro M. Baeza
# Copyright 2017 Tecnativa - Carlos Dauden <carlos.dauden@tecnativa.com>
# Copyright 2026 Studio73 - Pablo Cortés <pablo.cortes@studio73.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import Form

from .common import L10nEsPartnerCommon


class TestPartnerSearchAndDisplay(L10nEsPartnerCommon):
    def test_01_search_by_partner_and_commercial_name(self):
        partner_model = self.env["res.partner"]
        partner_ids = [partner[0] for partner in partner_model.name_search("prueba")]
        commercial_ids = [
            partner[0] for partner in partner_model.name_search("comercial")
        ]
        self.assertIn(self.partner.id, partner_ids)
        self.assertNotIn(
            self.partner.id,
            [
                partner[0]
                for partner in partner_model.name_search("prueba", operator="not ilike")
            ],
        )
        self.assertIn(
            self.partner,
            partner_model.search([("display_name", "ilike", "prueba")]),
        )
        self.assertNotIn(
            self.partner,
            partner_model.search([("display_name", "not ilike", "prueba")]),
        )
        self.assertIn(self.partner.id, commercial_ids)
        self.assertNotIn(
            self.partner.id,
            [
                partner[0]
                for partner in partner_model.name_search(
                    "comercial", operator="not ilike"
                )
            ],
        )
        self.assertIn(
            self.partner,
            partner_model.search([("display_name", "ilike", "comercial")]),
        )
        self.assertNotIn(
            self.partner,
            partner_model.search([("display_name", "not ilike", "comercial")]),
        )

    def test_02_name_pattern_formats_address_and_name_updates(self):
        self.env["ir.config_parameter"].sudo().set_str(
            "l10n_es_partner.name_pattern", "%(comercial_name)s (%(name)s)"
        )
        partner = (
            self.env["res.partner"]
            .sudo()
            .create(
                {
                    "name": "Empresa de prueba",
                    "comercial": "Nombre comercial",
                    "street": "My street",
                }
            )
        )
        expected_name = "Nombre comercial (Empresa de prueba)"
        self.assertEqual(partner.display_name, expected_name)
        self.assertEqual(partner.complete_name, expected_name)
        self.assertEqual(
            partner.with_context(show_address=True).display_name,
            f"{expected_name}\nMy street",
        )

        partner.write({"comercial": "Nombre actualizado"})
        expected_name = "Nombre actualizado (Empresa de prueba)"
        self.assertEqual(partner.display_name, expected_name)
        self.assertEqual(partner.complete_name, expected_name)

    def test_03_context_hides_commercial_name(self):
        self.env["ir.config_parameter"].sudo().set_str(
            "l10n_es_partner.name_pattern", "%(comercial_name)s (%(name)s)"
        )
        partner = (
            self.env["res.partner"]
            .sudo()
            .create({"name": "Empresa de prueba", "comercial": "Nombre comercial"})
        )
        self.assertEqual(
            partner.with_context(no_display_commercial=True).display_name,
            "Empresa de prueba",
        )

    def test_04_stored_name_keeps_commercial_name_when_hidden(self):
        """Renaming a company from a flow that hides the trade name doesn't
        remove it from the stored name, which sorts the contacts and is shown
        in their list"""
        self.env["ir.config_parameter"].sudo().set_str(
            "l10n_es_partner.name_pattern", "%(comercial_name)s (%(name)s)"
        )
        legal_partner = self.partner.with_context(no_display_commercial=True)
        legal_partner.name = "Empresa renombrada"
        self.assertEqual(legal_partner.display_name, "Empresa renombrada")
        self.assertEqual(
            self.partner.complete_name, "Nombre comercial (Empresa renombrada)"
        )
        self.assertEqual(
            self.partner.display_name, "Nombre comercial (Empresa renombrada)"
        )


class TestPartnerCommercialFieldSync(L10nEsPartnerCommon):
    def test_01_commercial_name_is_copied_to_child_contacts(self) -> None:
        child = self.env["res.partner"].create(
            {"name": "Contacto hijo", "parent_id": self.partner.id}
        )
        self.assertEqual(child.comercial, self.partner.comercial)

        self.partner.write({"comercial": "Nombre actualizado"})
        self.assertEqual(child.comercial, "Nombre actualizado")


class TestPartnerCommercialNameVisibility(L10nEsPartnerCommon):
    def test_01_name_is_visible_for_individuals_and_hidden_for_children(self) -> None:
        partner_model = self.env["res.partner"]
        for view_xmlid in ("base.view_partner_form", "base.view_partner_simple_form"):
            view = self.env.ref(view_xmlid)
            with Form(partner_model, view=view) as partner_form:
                partner_form.name = "Autónomo sin NIF"
                partner_form.email = "autonomo@example.test"
                partner_form.comercial = "Bar Pepe"
            self.assertFalse(partner_form.record.is_company)
            self.assertEqual(partner_form.record.comercial, "Bar Pepe")

            with Form(partner_model, view=view) as child_form:
                child_form.name = "Contacto hijo"
                child_form.parent_id = self.partner
                child_form.email = "contacto@example.test"
                with self.assertRaises(AssertionError):
                    child_form.comercial = "Nombre oculto"
