# Copyright 2017 Diagram Software S.L.
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


import base64
import contextlib
import logging
import os
import tempfile

from odoo import fields, models, release
from odoo.exceptions import ValidationError
from odoo.tools import config

_logger = logging.getLogger(__name__)

try:
    import cryptography
    from cryptography import x509
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.serialization import pkcs12

    CRYPTOGRAPHY_VERSION_3 = tuple(map(int, cryptography.__version__.split("."))) >= (
        3,
        0,
    )
    if not CRYPTOGRAPHY_VERSION_3:
        from cryptography.hazmat.backends import default_backend

        def load_key_and_certificates(*args, **kwargs):
            return pkcs12.load_key_and_certificates(
                *args, **kwargs, backend=default_backend()
            )

    else:
        load_key_and_certificates = pkcs12.load_key_and_certificates
except (ImportError, IOError) as err:
    _logger.debug(err)

# FIXME To be removed in v16, as it is now specified in the manifest
if tuple(map(int, cryptography.__version__.split("."))) < (3, 0):
    _logger.warning(
        "Cryptography version is not supported. Upgrade to 3.0.0 or greater."
    )


@contextlib.contextmanager
def pfx_to_pem(p12, directory=None):
    with tempfile.NamedTemporaryFile(
        prefix="private_", suffix=".pem", delete=False, dir=directory
    ) as t_pem:
        with open(t_pem.name, "wb") as f_pem:
            f_pem.write(
                p12[0].private_bytes(
                    serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )
            f_pem.close()
        yield t_pem.name


@contextlib.contextmanager
def pfx_to_crt(p12, directory=None):
    with tempfile.NamedTemporaryFile(
        prefix="public_", suffix=".crt", delete=False, dir=directory
    ) as t_crt:
        with open(t_crt.name, "wb") as f_crt:
            f_crt.write(p12[1].public_bytes(serialization.Encoding.PEM))
            f_crt.close()
        yield t_crt.name


class L10nEsAeatCertificatePassword(models.TransientModel):
    _name = "l10n.es.aeat.certificate.password"
    _description = "Wizard to Load AEAT Certificate"

    password = fields.Char(required=True)

    def get_keys(self):
        record = self.env["l10n.es.aeat.certificate"].browse(
            self.env.context.get("active_id")
        )
        directory = os.path.join(
            os.path.abspath(config["data_dir"]),
            "certificates",
            release.series,
            self.env.cr.dbname,
            record.folder,
        )
        file = base64.decodebytes(record.file)
        try:
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            pfx_password = self.password
            if isinstance(pfx_password, str):
                pfx_password = bytes(pfx_password, "utf-8")
            p12 = load_key_and_certificates(file, pfx_password)
            vals = self._process_certificate_vals(record, p12, directory)
            record.write(vals)
        except Exception as e:
            if e.args:
                args = list(e.args)
            raise ValidationError(args[-1]) from e

    def _process_certificate_vals(self, record, p12, directory):
        vals = {}
        with pfx_to_pem(p12, directory) as private_key:
            vals["private_key"] = private_key
        with pfx_to_crt(p12, directory) as public_key:
            vals["public_key"] = public_key
        certificate = p12[1]
        vals["date_start"] = certificate.not_valid_before
        vals["date_end"] = certificate.not_valid_after
        if not record.name:
            name = certificate.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)
            if name:
                vals["name"] = name[0].value
        return vals
