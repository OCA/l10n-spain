# Copyright 2023 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import logging

from cryptography import x509
from cryptography.hazmat.primitives import serialization

from odoo import models

from odoo.addons.l10n_es_facturae_face.models.wsse_signature import MemorySignature

_logger = logging.getLogger(__name__)
try:
    from zeep import Client
except (ImportError, IOError) as err:
    _logger.info(err)


class ResCompany(models.Model):

    _inherit = "res.company"

    def _get_faceb2b_wsdl_client(self):
        self.ensure_one()
        public_crt, private_key = self.env["l10n.es.aeat.certificate"].get_certificates(
            self
        )
        with open(public_crt, "rb") as f:
            cert = x509.load_pem_x509_certificate(f.read())
        with open(private_key, "rb") as f:
            key = serialization.load_pem_private_key(f.read(), None)
        return Client(
            wsdl=self.env["ir.config_parameter"]
            .sudo()
            .get_param("facturae.faceb2b.ws"),
            wsse=MemorySignature(
                cert,
                key,
                x509.load_pem_x509_certificate(
                    base64.b64decode(
                        self.env.ref("l10n_es_facturae_face.face_certificate").datas
                    )
                ),
            ),
        )
