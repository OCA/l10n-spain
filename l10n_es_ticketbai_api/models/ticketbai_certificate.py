# Copyright 2021 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)

try:
    from OpenSSL import crypto
except(ImportError, IOError) as err:
    _logger.error(err)


class TicketBaiCertificate(models.Model):
    _name = 'tbai.certificate'
    _description = 'TicketBAI Certificate for signing the XML files'

    name = fields.Char(required=True)
    company_id = fields.Many2one(
        string='Company', comodel_name='res.company', required=True,
        default=lambda self: self.env.user.company_id.id)
    datas = fields.Binary('P12 Certificate', required=True, attachment=True)
    password = fields.Char(default='')

    def get_p12_buffer(self):
        """
        :return: p12 Buffer
        """
        self.ensure_one()
        return base64.decodebytes(self.datas)

    def get_p12(self):
        """
        :return: OpenSSL.crypto.PKCS12
        """
        self.ensure_one()
        return crypto.load_pkcs12(self.get_p12_buffer(), self.password)
