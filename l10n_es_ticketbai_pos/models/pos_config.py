# Copyright 2021 Binovo IT Human Project SL
# Copyright 2022 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import logging

from odoo import _, exceptions, fields, models

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

    def get_tbai_p12_and_friendlyname(self):
        self.ensure_one()
        record = self.sudo()
        if record.tbai_enabled:
            if record.tbai_certificate_id:
                # Serialize new PKCS12 unencrypted object
                p12 = record.tbai_certificate_id.get_p12()
                p12_priv_key = p12[0]
                p12_cert = p12[1]
                p12_friendlyname = record.tbai_certificate_id.name.encode("utf-8")
                p12_password = record.tbai_certificate_id.password.encode()
                p12_encryption = BestAvailableEncryption(p12_password)
                certificate = pkcs12.serialize_key_and_certificates(
                    p12_friendlyname, p12_priv_key, p12_cert, None, p12_encryption
                )

                tbai_p12 = base64.b64encode(certificate)
                tbai_p12_friendlyname = p12_friendlyname
            else:
                p12 = record.company_id.tbai_aeat_certificate_id.get_p12()
                p12_priv_key = p12[0]
                p12_cert = p12[1]
                p12_friendlyname = (
                    record.company_id.tbai_aeat_certificate_id.name.encode("utf-8")
                )
                p12_encryption = NoEncryption()
                p12_password = False
                certificate = pkcs12.serialize_key_and_certificates(
                    p12_friendlyname, p12_priv_key, p12_cert, None, p12_encryption
                )
                tbai_p12 = base64.b64encode(certificate)
                tbai_p12_friendlyname = p12_friendlyname
        else:
            tbai_p12 = None
            tbai_p12_friendlyname = None
        return tbai_p12, tbai_p12_friendlyname, p12_password

    def open_ui(self):
        self.ensure_one()
        if self.tbai_enabled and not self.iface_l10n_es_simplified_invoice:
            raise exceptions.ValidationError(
                _("Simplified Invoice IDs Sequence is required")
            )
        return super().open_ui()

    def open_session_cb(self):
        self.ensure_one()
        if self.tbai_enabled and not self.iface_l10n_es_simplified_invoice:
            raise exceptions.ValidationError(
                _("Simplified Invoice IDs Sequence is required")
            )
        return super().open_session_cb()

    def open_existing_session_cb(self):
        self.ensure_one()
        if self.tbai_enabled and not self.iface_l10n_es_simplified_invoice:
            raise exceptions.ValidationError(
                _("Simplified Invoice IDs Sequence is required")
            )
        return super().open_existing_session_cb()
