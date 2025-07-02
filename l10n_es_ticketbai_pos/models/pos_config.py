# Copyright 2021 Binovo IT Human Project SL
# Copyright 2022 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import logging

from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)

try:
    from cryptography.hazmat.primitives.serialization import (
        BestAvailableEncryption,
        NoEncryption,
        pkcs12,
    )
except (ImportError, IOError) as err:
    _logger.error(err)


class PosConfig(models.Model):
    _inherit = "pos.config"

    tbai_enabled = fields.Boolean(related="company_id.tbai_enabled", readonly=True)
    tbai_device_serial_number = fields.Char(string="Device Serial Number")
    tbai_last_invoice_id = fields.Many2one(
        string="Last TicketBAI Invoice sent", comodel_name="tbai.invoice", copy=False
    )
    tbai_certificate_id = fields.Many2one(
        comodel_name="tbai.certificate",
        string="TicketBAI Certificate",
        domain="[('company_id', '=', company_id)]",
        copy=False,
    )
    iface_l10n_es_simplified_invoice = fields.Boolean(default=True)

    def _get_certificate_details(self, certificate):
        p12 = certificate.get_p12()
        return p12[0], p12[1], certificate.name.encode("utf-8")

    def get_tbai_p12_and_friendlyname(self):
        self.ensure_one()
        record = self.sudo()
        if record.tbai_enabled:
            cert = (
                record.tbai_certificate_id or record.company_id.tbai_aeat_certificate_id
            )
            p12_priv_key, p12_cert, p12_friendlyname = self._get_certificate_details(
                cert
            )
            p12_password = (
                cert.password.encode() if cert == record.tbai_certificate_id else False
            )
            p12_encryption = (
                BestAvailableEncryption(p12_password)
                if p12_password
                else NoEncryption()
            )
            certificate = pkcs12.serialize_key_and_certificates(
                p12_friendlyname, p12_priv_key, p12_cert, None, p12_encryption
            )
            return base64.b64encode(certificate), p12_friendlyname, p12_password
        return None, None, None

    @api.constrains("iface_l10n_es_simplified_invoice")
    def _check_tbai(self):
        if self.tbai_enabled and not self.iface_l10n_es_simplified_invoice:
            raise exceptions.ValidationError(
                _("Simplified Invoice IDs Sequence is required")
            )

    def open_existing_session_cb(self):
        self.ensure_one()
        self._check_tbai()
        return super().open_existing_session_cb()
