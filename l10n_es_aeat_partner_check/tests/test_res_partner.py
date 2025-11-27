# Copyright 2021 Studio73 - Ethan Hildick <ethan@studio73.es>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from unittest import mock

import requests

from odoo.tests import common

soap_model = "odoo.addons.l10n_es_aeat.models.aeat_soap.L10nEsAeatSoap"
cert_model = "odoo.addons.l10n_es_aeat.models.aeat_certificate.L10nEsAeatCertificate"
partner_model = "odoo.addons.l10n_es_aeat_partner_check.models.res_partner.ResPartner"

# We mock all API requests here as to not send unnecessary load to an external API
# nor risk a blocked repo if said API is down


class TestResPartner(common.SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        cls._super_send = requests.Session.send
        super().setUpClass()
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

    @classmethod
    def _request_handler(cls, s, r, /, **kw):
        """Don't block external requests."""
        return cls._super_send(s, r, **kw)

    @mock.patch(
        f"{soap_model}.send_soap",
        return_value=[
            {
                "Nombre": "Mr. Odoo & Co.",
                "Nif": "ESA12345674",
                "Resultado": "IDENTIFICADO",
            }
        ],
    )
    @mock.patch(  # we ignore the aeat_check_re in this test to test it individually
        f"{partner_model}.aeat_check_re", return_value=True
    )
    def test_01_check_partner(self, redirect_mock, *args):
        self.assertFalse(self.partner.aeat_partner_check_result)
        self.partner.aeat_check_partner()
        self.assertEqual(self.partner.aeat_partner_check_result, "IDENTIFICADO")

    @mock.patch(f"{cert_model}.get_certificates", return_value=("123123", "456456"))
    @mock.patch("requests.post")
    def test_02_aeat_check_re(self, redirect_mock, *args):
        self.assertFalse(self.partner.aeat_partner_type)
        redirect_mock.return_value.content = b"aihjsb NIF no sometido asjidnasdhsb"
        self.partner.aeat_check_re()
        self.assertEqual(self.partner.aeat_partner_type, "standard")
        redirect_mock.return_value.content = b"aihjsb NIF sometido asjidnasdhsb"
        self.partner.aeat_check_re()
        self.assertEqual(self.partner.aeat_partner_type, "sales_equalization")

    @mock.patch(
        f"{soap_model}.send_soap",
        return_value=[
            {
                "Nombre": "Block no. 401",
                "Nif": "36BBBFF5679L8ZR",
                "Resultado": "IDENTIFICADO",
            }
        ],
    )
    @mock.patch(  # we ignore the aeat_check_re in this test to test it individually
        f"{partner_model}.aeat_check_re", return_value=True
    )
    def test_03_check_partner_no_spanish(self, redirect_mock, *args):
        self.assertFalse(self.partner_in.aeat_partner_check_result)
        self.partner_in.aeat_check_partner()
        self.assertFalse(self.partner_in.aeat_partner_check_result)

    def test_04_write_check_partner(self):
        self.env.company.vat_check_aeat = False
        self.partner_in.write({"company_id": self.env.company.id})

    def test_05_compute_data_diff(self):
        self.partner.aeat_partner_check_result = "IDENTIFICADO"
        self.partner.name = "Mr. Odoo & Co."
        self.partner.aeat_partner_name = "Mr. Odoo & Co."
        self.assertFalse(
            self.partner.aeat_data_diff, "A-1: Names should match without diff"
        )
        self.partner.aeat_partner_name = "Mr. Odoo &  Co."  # Double space in AEAT name
        self.assertFalse(
            self.partner.aeat_data_diff,
            "A-2: Names should match despite AEAT double space",
        )
        self.partner.aeat_partner_name = "Mr. Odoo S.L."
        self.assertTrue(
            self.partner.aeat_data_diff,
            "B: Names should differ, aeat_data_diff should be True",
        )
