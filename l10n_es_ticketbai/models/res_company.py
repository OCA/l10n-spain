# Copyright 2021 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    tbai_aeat_certificate_id = fields.Many2one(
        comodel_name='l10n.es.aeat.certificate', string='AEAT Certificate',
        domain="[('state', '=', 'active'), ('company_id', '=', id)]", copy=False)

    @api.onchange('tbai_enabled')
    def onchange_tbai_enabled_unset_tbai_aeat_certificate_id(self):
        if not self.tbai_enabled:
            self.tbai_aeat_certificate_id = False

    def tbai_certificate_get_p12(self):
        if self.tbai_aeat_certificate_id:
            return self.tbai_aeat_certificate_id.get_p12()
        else:
            return super().tbai_certificate_get_p12()

    def tbai_certificate_get_public_key(self):
        if self.tbai_aeat_certificate_id:
            return self.tbai_aeat_certificate_id.public_key
        else:
            return None

    def tbai_certificate_get_private_key(self):
        if self.tbai_aeat_certificate_id:
            return self.tbai_aeat_certificate_id.private_key
        else:
            return None
