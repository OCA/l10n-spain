# Copyright 2021 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
from odoo import models, fields, api, exceptions, _


class PosConfig(models.Model):
    _inherit = 'pos.config'

    tbai_enabled = fields.Boolean(related='company_id.tbai_enabled', readonly=True)
    tbai_device_serial_number = fields.Char(string='Device Serial Number')
    tbai_last_invoice_id = fields.Many2one(
        string='Last TicketBAI Invoice sent', comodel_name='tbai.invoice', copy=False)
    tbai_certificate_id = fields.Many2one(
        comodel_name='tbai.certificate', string='TicketBAI Certificate',
        domain="[('company_id', '=', company_id)]", copy=False)
    iface_l10n_es_simplified_invoice = fields.Boolean(
        default=True
    )

    def get_tbai_p12_and_friendlyname(self):
        self.ensure_one()
        record = self.sudo()
        if record.tbai_enabled:
            if record.tbai_certificate_id:
                p12 = record.tbai_certificate_id.get_p12()
                tbai_p12 = base64.b64encode(p12.export())
                tbai_p12_friendlyname = p12.get_friendlyname()
            else:
                tbai_p12 = record.company_id.tbai_aeat_certificate_id.tbai_p12
                tbai_p12_friendlyname = \
                    record.company_id.tbai_aeat_certificate_id.tbai_p12_friendlyname
        else:
            tbai_p12 = None
            tbai_p12_friendlyname = None
        return tbai_p12, tbai_p12_friendlyname

    @api.multi
    def open_ui(self):
        self.ensure_one()
        if self.tbai_enabled and not self.iface_l10n_es_simplified_invoice:
            raise exceptions.ValidationError(
                _("Simplified Invoice IDs Sequence is required")
            )
        return super().open_ui()

    @api.multi
    def open_session_cb(self):
        self.ensure_one()
        if self.tbai_enabled and not self.iface_l10n_es_simplified_invoice:
            raise exceptions.ValidationError(
                _("Simplified Invoice IDs Sequence is required")
            )
        return super().open_session_cb()

    @api.multi
    def open_existing_session_cb(self):
        self.ensure_one()
        if self.tbai_enabled and not self.iface_l10n_es_simplified_invoice:
            raise exceptions.ValidationError(
                _("Simplified Invoice IDs Sequence is required")
            )
        return super().open_existing_session_cb()
