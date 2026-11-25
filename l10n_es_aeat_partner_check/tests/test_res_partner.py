# Copyright 2021 Studio73 - Ethan Hildick <ethan@studio73.es>
# Copyright 2026 Tecnativa - Carlos Dauden
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from unittest import mock

from odoo import Command

from odoo.addons.base.tests.common import BaseCommon

# The AEAT services are external: the census check goes through the SOAP
# client of l10n_es_aeat and the equivalence surcharge check through
# requests. Only those calls are mocked.
SEND_SOAP = "odoo.addons.l10n_es_aeat.models.aeat_soap.L10nEsAeatSoap.send_soap"
REQUESTS_POST = (
    "odoo.addons.l10n_es_aeat_partner_check.models.res_partner.requests.post"
)


class TestResPartner(BaseCommon):
    _test_user_groups = ("base.group_user", "base.group_partner_manager")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Certificate files of the company, read when calling the AEAT
        config = cls.env["ir.config_parameter"].sudo()
        config.set_str("l10n_es_aeat_certificate.publicCrt", "/tmp/public.crt")
        config.set_str("l10n_es_aeat_certificate.privateKey", "/tmp/private.key")
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Mr. Odoo & Co.",
                "country_id": cls.env.ref("base.es").id,
                "vat": "ESA12345674",
            }
        )
        cls.partner_in = cls.env["res.partner"].create(
            {
                "name": "Block no. 401",
                "country_id": cls.env.ref("base.in").id,
                "vat": "36BBBFF5679L8ZR",
            }
        )

    def _census_answer(self, name, result="IDENTIFICADO", vat="A12345674"):
        return [{"Nombre": name, "Nif": vat, "Resultado": result}]

    def _surcharge_answer(self, post, subject):
        post.return_value.content = (
            b"<p>NIF sometido</p>" if subject else b"<p>NIF no sometido</p>"
        )

    def test_check_partner(self):
        with (
            mock.patch(
                SEND_SOAP, return_value=self._census_answer("Mr. Odoo & Co.")
            ) as send_soap,
            mock.patch(REQUESTS_POST) as post,
        ):
            self._surcharge_answer(post, subject=False)
            self.partner.aeat_check_partner()
        self.assertEqual(send_soap.call_args.args[-1]["Nif"], "A12345674")
        self.assertEqual(post.call_args.kwargs["params"]["nif"], "A12345674")
        self.assertEqual(
            post.call_args.kwargs["cert"], ("/tmp/public.crt", "/tmp/private.key")
        )
        self.assertEqual(self.partner.aeat_partner_check_result, "IDENTIFICADO")
        self.assertEqual(self.partner.aeat_partner_name, "Mr. Odoo & Co.")
        self.assertEqual(self.partner.aeat_partner_vat, "A12345674")
        self.assertEqual(self.partner.aeat_partner_type, "standard")
        self.assertFalse(self.partner.aeat_data_diff)
        self.assertTrue(self.partner.aeat_last_checked)

    def test_check_partner_not_identified(self):
        with (
            mock.patch(SEND_SOAP, return_value=[]),
            mock.patch(REQUESTS_POST) as post,
        ):
            self._surcharge_answer(post, subject=False)
            self.partner.aeat_check_partner()
        self.assertEqual(self.partner.aeat_partner_check_result, "NO IDENTIFICABLE")
        self.assertFalse(self.partner.aeat_partner_name)

    def test_check_equivalence_surcharge(self):
        with mock.patch(REQUESTS_POST) as post:
            self._surcharge_answer(post, subject=False)
            self.partner.aeat_check_re()
            self.assertEqual(self.partner.aeat_partner_type, "standard")
            self._surcharge_answer(post, subject=True)
            self.partner.aeat_check_re()
        self.assertEqual(self.partner.aeat_partner_type, "sales_equalization")

    def test_check_partner_no_spanish(self):
        with (
            mock.patch(SEND_SOAP) as send_soap,
            mock.patch(REQUESTS_POST) as post,
        ):
            self.partner_in.aeat_check_partner()
        send_soap.assert_not_called()
        post.assert_not_called()
        self.assertFalse(self.partner_in.aeat_partner_check_result)

    def test_automatic_check(self):
        partner_vals = {
            "name": "New partner",
            "country_id": self.env.ref("base.es").id,
            "vat": "ESB12345674",
        }
        with (
            mock.patch(SEND_SOAP) as send_soap,
            mock.patch(REQUESTS_POST) as post,
        ):
            partner = self.env["res.partner"].create(partner_vals)
            partner.name = "New partner renamed"
        send_soap.assert_not_called()
        post.assert_not_called()
        settings = self.env["res.config.settings"].sudo().create({})
        settings.vat_check_aeat = True
        settings.execute()
        self.assertTrue(self.env.company.vat_check_aeat)
        with (
            mock.patch(
                SEND_SOAP, return_value=self._census_answer("NEW PARTNER")
            ) as send_soap,
            mock.patch(REQUESTS_POST) as post,
        ):
            self._surcharge_answer(post, subject=True)
            partner = self.env["res.partner"].create(partner_vals)
            self.assertEqual(send_soap.call_count, 1)
            self.assertEqual(partner.aeat_partner_check_result, "IDENTIFICADO")
            self.assertEqual(partner.aeat_partner_type, "sales_equalization")
            self.assertTrue(partner.aeat_data_diff)
            partner.name = "NEW PARTNER"
            self.assertEqual(send_soap.call_count, 2)
            self.assertFalse(partner.aeat_data_diff)
            partner.email = "new.partner@example.com"
            self.assertEqual(send_soap.call_count, 2)

    def test_automatic_check_without_spanish_nif(self):
        """Partners without a Spanish NIF are not sent to the AEAT, which
        can't identify them"""
        self.env.company.sudo().vat_check_aeat = True
        with (
            mock.patch(SEND_SOAP, return_value=[]) as send_soap,
            mock.patch(REQUESTS_POST) as post,
        ):
            partner = self.env["res.partner"].create(
                {"name": "Without VAT", "country_id": self.env.ref("base.es").id}
            )
            partner.name = "Without VAT renamed"
            passport_partner = self.env["res.partner"].create(
                {
                    "name": "With passport",
                    "country_id": self.env.ref("base.es").id,
                    "l10n_es_passport": "PAB123456",
                }
            )
            passport_partner.name = "With passport renamed"
        send_soap.assert_not_called()
        post.assert_not_called()
        self.assertFalse(
            (partner | passport_partner).filtered("aeat_partner_check_result")
        )

    def test_automatic_check_active_company(self):
        """The automatic check follows the active company, the same when the
        partner is created and when it is updated"""
        company_b = (
            self.env["res.company"]
            .sudo()
            .create({"name": "Company B", "vat_check_aeat": True})
        )
        self.env.user.sudo().company_ids = [Command.link(company_b.id)]
        self.assertFalse(self.env.user.company_id.vat_check_aeat)
        with (
            mock.patch(
                SEND_SOAP,
                return_value=self._census_answer("SHARED PARTNER", vat="B12345674"),
            ) as send_soap,
            mock.patch(REQUESTS_POST) as post,
        ):
            self._surcharge_answer(post, subject=False)
            partner = (
                self.env["res.partner"]
                .with_company(company_b)
                .create(
                    {
                        "name": "Shared partner",
                        "country_id": self.env.ref("base.es").id,
                        "vat": "ESB12345674",
                    }
                )
            )
            self.assertEqual(send_soap.call_count, 1)
            partner.name = "SHARED PARTNER"
        self.assertEqual(send_soap.call_count, 2)
        self.assertFalse(partner.aeat_data_diff)

    def test_compute_data_diff(self):
        partner = self.partner.sudo()
        partner.aeat_partner_check_result = "IDENTIFICADO"
        partner.aeat_partner_name = "Mr. Odoo & Co."
        self.assertFalse(
            self.partner.aeat_data_diff, "A-1: Names should match without diff"
        )
        partner.aeat_partner_name = "Mr. Odoo &  Co."  # Double space in AEAT name
        self.assertFalse(
            self.partner.aeat_data_diff,
            "A-2: Names should match despite AEAT double space",
        )
        partner.aeat_partner_name = "Mr. Odoo S.L."
        self.assertTrue(
            self.partner.aeat_data_diff,
            "B: Names should differ, aeat_data_diff should be True",
        )
