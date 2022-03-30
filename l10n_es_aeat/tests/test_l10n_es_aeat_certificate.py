# Copyright 2021 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import base64
from datetime import datetime, timedelta

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import BestAvailableEncryption, pkcs12
from cryptography.x509 import oid

from odoo import exceptions
from odoo.tests import common


class TestL10nEsAeatCertificateBase(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.certificate_password = b"794613"
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()
        builder = x509.CertificateBuilder()
        cls.certificate_name = "Test Certificate"
        one_day = timedelta(1, 0, 0)
        builder = (
            builder.subject_name(
                x509.Name(
                    [x509.NameAttribute(oid.NameOID.COMMON_NAME, cls.certificate_name)]
                )
            )
            .issuer_name(
                x509.Name(
                    [
                        x509.NameAttribute(oid.NameOID.COMMON_NAME, "cryptography.io"),
                    ]
                )
            )
            .not_valid_before(datetime.today() - one_day)
            .not_valid_after(datetime.today() + (one_day * 30))
            .serial_number(x509.random_serial_number())
            .public_key(public_key)
        )
        certificate = builder.sign(private_key=private_key, algorithm=hashes.SHA256())
        content = pkcs12.serialize_key_and_certificates(
            None,
            private_key,
            certificate,
            None,
            BestAvailableEncryption(cls.certificate_password),
        )
        cls.sii_cert = cls.env["l10n.es.aeat.certificate"].create(
            {
                "folder": "Test folder",
                "file": base64.b64encode(content),
            }
        )

    def _activate_certificate(self, passwd=None):
        """Obtain Keys from .pfx and activate the cetificate"""
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
        self.assertEqual(self.certificate_name, self.sii_cert.name)


class TestL10nEsAeatCertificate(TestL10nEsAeatCertificateBase):
    def test_activate_certificate(self):
        self.assertRaises(
            exceptions.ValidationError,
            self._activate_certificate,
            b"Wrong passwd",
        )
        self._activate_certificate(self.certificate_password)
        self.assertEqual(self.sii_cert.state, "active")
