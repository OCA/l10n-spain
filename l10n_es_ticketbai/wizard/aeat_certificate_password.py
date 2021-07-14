# Copyright 2021 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
import base64
from odoo import models, api

_logger = logging.getLogger(__name__)

try:
    from OpenSSL import crypto
except(ImportError, IOError) as err:
    _logger.error(err)


class L10nEsAeatCertificatePassword(models.TransientModel):
    _inherit = 'l10n.es.aeat.certificate.password'

    @api.multi
    def get_keys(self):
        super().get_keys()
        record = self.env['l10n.es.aeat.certificate'].browse(
            self.env.context.get('active_id'))
        file = base64.decodebytes(record.file)
        p12 = crypto.load_pkcs12(file, self.password)
        record.tbai_p12_friendlyname = p12.get_friendlyname()
