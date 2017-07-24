# -*- coding: utf-8 -*-
# © 2017 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models, fields
import logging
try:
    from paramiko.client import SSHClient, RSAKey
except (ImportError, IOError) as err:
    logging.info(err)
import base64
from lxml import etree

in_path = '/in'
adjin_path = '/adjin'
statout_path = '/statout'


class AccountInvoiceIntegration(models.Model):
    _inherit = "account.invoice.integration.log"

    hub_message_id = fields.Char(readonly=True)

    def _efact_connect(self):
        connection = SSHClient()
        connection.get_host_keys().add(
            '[%s]:%s' % (
                self.env["ir.config_parameter"].get_param(
                    "account.invoice.efact.server", default=None),
                self.env["ir.config_parameter"].get_param(
                    "account.invoice.efact.port", default=None)
            ),
            'ssh-rsa',
            RSAKey(data=base64.b64decode(
                self.env["ir.config_parameter"].get_param(
                    "account.invoice.efact.key", default=None)))
        )
        connection.connect(
            hostname=self.env["ir.config_parameter"].get_param(
                "account.invoice.efact.server", default=None),
            port=int(self.env["ir.config_parameter"].get_param(
                "account.invoice.efact.port", default=None)),
            username=self.env["ir.config_parameter"].get_param(
                "account.invoice.efact.user", default=None),
            password=self.env["ir.config_parameter"].get_param(
                "account.invoice.efact.password", default=None)
        )
        sftp = connection.open_sftp()
        return connection, sftp

    def get_filename(self, annex=''):
        invoice = self.integration_id.invoice_id
        filename = invoice.partner_id.facturae_efact_code + '@'
        filename += invoice.company_id.partner_id.facturae_efact_code + '@'
        filename += invoice.number.replace('/', '_')
        if len(annex) > 0:
            filename += '@' + annex
        return filename

    def efact_transform_feedback(self, delivery_feedback, filename):
        hub_list = filename.rsplit('@', 1)
        hub_reference = hub_list[0]
        hub_message_id = hub_list[1]
        for status in delivery_feedback.findall('StatusFeedback'):
            hub_feedback = status.find('HubFeedback')
            invoice_feedback = status.find('InvoiceFeedback')
            feedback = invoice_feedback.find('Feedback')
            hub_id = hub_feedback.find('HubId').text
            integration = self.env['account.invoice.integration'].search([
                ('method_id', '=', self.env.ref(
                    'l10n_es_facturae_efact.integration_efact').id),
                ('efact_hub_id', '=', hub_id)
            ])
            if not integration:
                integration = self.env['account.invoice.integration'].search([
                    ('method_id', '=', self.env.ref(
                        'l10n_es_facturae_efact.integration_efact').id),
                    ('efact_hub_id', '=', False),
                    ('efact_reference', '=', hub_reference)
                ])
                integration.efact_hub_id = hub_id
                integration.register_number = feedback.find(
                    'RegisterNumber').text
            self.env['account.invoice.integration.log'].create({
                'type': 'update',
                'integration_id': integration.id,
                'state': 'sent',
                'log': feedback.find('Status').text,
                'hub_message_id': hub_message_id,
                'update_date': feedback.find('StatusDate').text
            })
            integration.integration_status = 'efact-' + feedback.find(
                'Status').text
            integration.integration_description = feedback.find('Reason').find(
                'Description').text
            for annex in feedback.findall('ElectronicAcknowledgment'):
                annex_name = integration.register_number + '.' + annex.find(
                    'formatType').text
                self.env['ir.attachment'].create({
                    'name': annex_name,
                    'datas': annex.find('document').text,
                    'datas_fname': annex_name,
                    'res_model': 'account.invoice.integration',
                    'res_id': integration.id,
                    'mimetype': 'application/xml'
                })

    def send_method(self):
        if self.integration_id.method_id == self.env.ref(
                'l10n_es_facturae_efact.integration_efact'):
            connection, sftp = self._efact_connect()
            try:
                path = sftp.normalize('.')
                sftp.chdir(path + in_path)
                file = sftp.open(self.get_filename(), 'w')
                file.write(
                    base64.b64decode(self.integration_id.attachment_id.datas)
                )
                file.flush()
                file.close()
                sftp.chdir(path + adjin_path)
                if self.integration_id.attachment_ids:
                    integer = 1
                    for attachment in self.integration_id.attachment_ids:
                        logging.info(attachment.name.split('.'))
                        annex = sftp.open(
                            self.get_filename(
                                '%03d.%s' % (
                                    integer,
                                    attachment.name.split('.')[-1])
                            ),
                            'w'
                        )
                        annex.write(base64.b64decode(attachment.datas))
                        annex.flush()
                        annex.close()
                        integer += 1
            except IOError as error:
                self.state = 'failed'
                self.integration_id.state = 'failed'
                self.log = error
                return
            self.state = 'sent'
            self.integration_id.efact_reference = self.get_filename()
            self.integration_id.state = 'sent'
            self.integration_id.can_send = False
            self.integration_id.can_cancel = False
            self.integration_id.can_update = False
            sftp.close()
            connection.close()
            return
        return super(AccountInvoiceIntegration, self).send_method()

    def efact_check_history(self):
        connection, sftp = self._efact_connect()
        path = sftp.normalize('ssh')
        sftp.chdir(path + statout_path)
        attrs = sftp.listdir_attr('.')
        attrs.sort(key=lambda attr: attr.st_atime)
        for attr in attrs:
            file = sftp.open(attr.filename)
            filetext = file.read()
            file.close()
            feedback = etree.fromstring(filetext)
            self.efact_transform_feedback(feedback, attr.filename)
            sftp.remove(attr.filename)
        sftp.close()
        connection.close()
