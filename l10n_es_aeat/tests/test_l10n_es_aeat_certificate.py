# Copyright 2021 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import base64
from datetime import datetime, timedelta

import cryptography
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import (
    BestAvailableEncryption,
    Encoding,
    pkcs12,
)
from cryptography.x509 import oid

from odoo import exceptions
from odoo.tests import Form, common

CRYPTOGRAPHY_VERSION_3 = tuple(map(int, cryptography.__version__.split("."))) >= (3, 0)
if not CRYPTOGRAPHY_VERSION_3:
    from cryptography.hazmat.backends import default_backend

    def generate_private_key(public_exponent, key_size):
        return rsa.generate_private_key(
            public_exponent=public_exponent,
            key_size=key_size,
            backend=default_backend(),
        )

    from OpenSSL import crypto

    def serialize_key_and_certificates(private_key, certificate, password):
        p12 = crypto.PKCS12()
        p12.set_privatekey(
            crypto.load_privatekey(
                crypto.FILETYPE_PEM,
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                ),
            )
        )
        p12.set_certificate(
            crypto.load_certificate(
                crypto.FILETYPE_PEM,
                certificate.public_bytes(
                    encoding=serialization.Encoding.PEM,
                ),
            )
        )
        p12data = p12.export(password)
        return p12data

else:
    generate_private_key = rsa.generate_private_key

    def serialize_key_and_certificates(private_key, certificate, password):
        return pkcs12.serialize_key_and_certificates(
            None,
            private_key,
            certificate,
            None,
            BestAvailableEncryption(password),
        )


class TestL10nEsAeatCertificateBase(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.certificate_password = b"794613"
        private_key = generate_private_key(public_exponent=65537, key_size=2048)
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
        sign_params = {"private_key": private_key, "algorithm": hashes.SHA256()}
        if not CRYPTOGRAPHY_VERSION_3:
            sign_params["backend"] = default_backend()
        certificate = builder.sign(**sign_params)
        content = serialize_key_and_certificates(
            private_key,
            certificate,
            cls.certificate_password,
        )
        cls.public_key = certificate.public_bytes(Encoding.PEM).decode("UTF-8")
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

    def test_show_public_key(self):
        self._activate_certificate(self.certificate_password)
        with Form(self.sii_cert) as f:
            self.assertFalse(f.show_public_key)
            self.assertFalse(f.public_key_data)
            f.show_public_key = True
            self.assertTrue(f.public_key_data)
            self.assertEqual(f.public_key_data, self.public_key)
            f.show_public_key = False
            self.assertFalse(f.public_key_data)
