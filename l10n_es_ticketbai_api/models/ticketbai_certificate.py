# Copyright 2021 Binovo IT Human Project SL
# Copyright 2021 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)

try:
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.serialization import pkcs12
except (ImportError, IOError) as err:
    _logger.error(err)


class TicketBaiCertificate(models.Model):
    _name = "tbai.certificate"
    _description = "TicketBAI Certificate for signing the XML files"

    name = fields.Char(required=True)
    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.user.company_id.id,
    )
    datas = fields.Binary("P12 Certificate", required=True, attachment=True)
    password = fields.Char(default="")

    def get_p12_buffer(self):
        """
        :return: p12 Buffer
        """
        self.ensure_one()
        return base64.decodebytes(self.datas)

    def get_p12(self):
        """
        :return: cryptography.pkcs12
        """
        self.ensure_one()
        return pkcs12.load_key_and_certificates(
            self.get_p12_buffer(), self.password.encode(), backend=default_backend()
        )
