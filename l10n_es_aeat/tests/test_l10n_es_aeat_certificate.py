# Copyright 2021 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import base64

from odoo import exceptions
from odoo.modules.module import get_resource_path
from odoo.tests import common


class TestL10nEsAeatCertificateBase(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.certificate_path = get_resource_path(
            "l10n_es_aeat",
            "tests",
            "cert",
            "entidadspj_act.p12",
        )
        cls.certificate_password = b"794613"
        with open(cls.certificate_path, "rb") as certificate:
            content = certificate.read()
        cls.sii_cert = cls.env["l10n.es.aeat.certificate"].create(
            {
                "name": "Test Certificate",
                "folder": "Test folder",
                "file": base64.b64encode(content),
            }
        )

    def _activate_certificate(self, passwd=None):
        """  Obtain Keys from .pfx and activate the cetificate """
        if not passwd:
            passwd = self.certificate_password
        wizard = self.env["l10n.es.aeat.certificate.password"].create(
            {"password": passwd}
        )
        wizard.with_context(active_id=self.sii_cert.id).get_keys()
        self.sii_cert.action_active()
        self.sii_cert.company_id.write(
            {"name": "ENTIDAD FICTICIO ACTIVO", "vat": "ESJ7102572J"}
        )


class TestL10nEsAeatCertificate(TestL10nEsAeatCertificateBase):
    def test_activate_certificate(self):
        self.assertRaises(
            exceptions.ValidationError,
            self._activate_certificate,
            b"Wrong passwd",
        )
        self._activate_certificate(self.certificate_password)
        self.assertEqual(self.sii_cert.state, "active")
