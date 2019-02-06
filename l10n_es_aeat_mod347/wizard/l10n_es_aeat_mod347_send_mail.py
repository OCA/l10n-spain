from openerp import api, models


class L10nEsAeatMod347SendMail(models.TransientModel):
    _name = 'l10n.es.aeat.mod347.send.mail'

    @api.multi
    def send_emails(self):
        PartnerRecord = self.env['l10n.es.aeat.mod347.partner_record']
        partner_record_ids = self.env.context.get('active_ids', [])
        PartnerRecord.browse(partner_record_ids).send_email_direct()
