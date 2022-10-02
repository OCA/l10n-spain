# Copyright 2021 Binovo IT Human Project SL
# Copyright 2021 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import logging

from odoo import models

_logger = logging.getLogger(__name__)

try:
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.serialization import pkcs12
except (ImportError, IOError) as err:
    _logger.error(err)


class L10nEsAeatCertificatePassword(models.TransientModel):
    _inherit = "l10n.es.aeat.certificate.password"

    def get_keys(self):
        ret = super().get_keys()
        record = self.env["l10n.es.aeat.certificate"].browse(
            self.env.context.get("active_id")
        )
        file = base64.decodebytes(record.file)
        password = self.password
        if isinstance(password, str):
            password = bytes(password, "utf-8")
        p12 = pkcs12.load_key_and_certificates(
            file, password, backend=default_backend()
        )
        record.tbai_p12_friendlyname = bytes(str(p12[1].subject), "utf-8")
        return ret
