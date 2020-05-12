# -*- coding: utf-8 -*-
# Copyright 2020 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
from odoo import models, fields, api, _, exceptions

_logger = logging.getLogger(__name__)

try:
    from OpenSSL import crypto
except(ImportError, IOError) as err:
    _logger.error(err)


class L10nEsTicketBaiCertificate(models.Model):
    _name = 'l10n.es.ticketbai.certificate'
    _description = 'TicketBai Certificate'

    name = fields.Char(string="Name")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active')
    ], string="State", default="draft")
    file = fields.Binary(string="File", required=True)
    folder = fields.Char(string="Folder Name", required=True)
    date_start = fields.Date(string="Start Date")
    date_end = fields.Date(string="End Date")
    public_key = fields.Char(string="Public Key", readonly=True)
    private_key = fields.Char(string="Private Key", readonly=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Compañía",
        required=True,
        default=lambda self: self.env.user.company_id.id
    )

    @api.multi
    def load_password_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Insert Password'),
            'res_model': 'l10n.es.ticketbai.certificate.password',
            'view_mode': 'form',
            'view_type': 'form',
            'views': [(False, 'form')],
            'target': 'new',
        }

    @api.multi
    def action_active(self):
        self.ensure_one()
        other_configs = self.search([('id', '!=', self.id),
                                     ('company_id', '=', self.company_id.id)])
        for config_id in other_configs:
            config_id.state = 'draft'
        self.state = 'active'

    @api.multi
    def get_certificates(self, company=False):
        if not company:
            company = self.env.user.company_id
        today = fields.Date.today()
        aeat_certificate = self.search([
            ('company_id', '=', company.id),
            ('public_key', '!=', False),
            ('private_key', '!=', False),
            '|', ('date_start', '=', False),
            ('date_start', '<=', today),
            '|', ('date_end', '=', False),
            ('date_end', '>=', today),
            ('state', '=', 'active')
        ], limit=1)
        if aeat_certificate:
            public_crt = aeat_certificate.public_key
            private_key = aeat_certificate.private_key
        else:
            public_crt = self.env['ir.config_parameter'].get_param(
                'l10n_es_ticketbai_certificate.publicCrt', False)
            private_key = self.env['ir.config_parameter'].get_param(
                'l10n_es_ticketbai_certificate.privateKey', False)
        if not public_crt or not private_key:
            raise exceptions.Warning(
                _("Error! There aren't certificates.")
            )
        return public_crt, private_key

    def get_p12(self):
        """
        Because for signing the XML file is needed a PKCS #12 and
        the passphrase is not available in the AEAT certificate,
        create a new one and set the certificate and its private key
        from the stored files.
        :return: A PKCS #12 archive
        """
        self.ensure_one()
        with open(self.public_key, 'rb') as f_crt:
            cert = crypto.load_certificate(crypto.FILETYPE_PEM, f_crt.read())
        p12 = crypto.PKCS12()
        p12.set_certificate(cert)
        with open(self.private_key, 'rb') as f_pem:
            private_key = f_pem.read()
        p12.set_privatekey(crypto.load_privatekey(crypto.FILETYPE_PEM, private_key))
        return p12
