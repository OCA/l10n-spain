# Copyright 2016-2017 Tecnativa - Pedro M. Baeza
# Copyright 2017 Tecnativa - Carlos Dauden <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3).

import io
from unittest.mock import patch

import xlwt

from odoo.tests import common, tagged

WIZARD_LOGGER = "odoo.addons.l10n_es_partner.wizard.l10n_es_partner_wizard"


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
        # Import banks from Internet, with a mocked file of the Bank of Spain
        bde_sample = {
            "COD_BE": "0182",
            "NOMCOMERCIAL": "BBVA",
            "NOMBRE105": "BANCO BILBAO VIZCAYA ARGENTARIA, S.A.",
            "CODPOSTAL": "48005",
            "CODIGOCIF": "A48265169",
        }
        buf = io.BytesIO()
        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet("Bancos")
        for col, (header, value) in enumerate(bde_sample.items()):
            sheet.write(0, col, header)
            sheet.write(1, col, value)
        workbook.save(buf)
        with (
            patch("requests.get") as mock_get,
            self.assertNoLogs(WIZARD_LOGGER, "WARNING"),
        ):
            mock_get.return_value.content = buf.getvalue()
            self.wizard.execute()
        bank = self.env["res.bank"].search([("code", "=", "0182")])
        self.assertTrue(bank)
        self.assertEqual(bank.state, self.env.ref("base.state_es_bi"))
        bank.unlink()
        # Import banks again from Internet: the tests block the external
        # requests, so the wizard falls back on the local file
        with self.assertLogs(WIZARD_LOGGER, "WARNING"):
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


@tagged("external_l10n", "external", "-standard")
class TestL10nEsPartnerExternal(common.TransactionCase):  # pragma: no cover
    """Download the banks from the Bank of Spain. Run on purpose with
    ``--test-tags=external_l10n``: without the standard tag, Odoo does not
    block the external requests."""

    def test_import_banks_from_internet(self):
        self.env["res.bank"].search([("code", "=", "0182")]).unlink()
        with self.assertNoLogs(WIZARD_LOGGER, "WARNING"):
            self.env["l10n.es.partner.import.wizard"].create({}).execute()
        self.assertTrue(self.env["res.bank"].search([("code", "=", "0182")]))
