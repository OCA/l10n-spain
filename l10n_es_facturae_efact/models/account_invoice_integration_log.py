# © 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import models, fields
import logging
try:
    from paramiko.client import SSHClient
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
        ICP = self.env["ir.config_parameter"].sudo()
        connection = SSHClient()
        connection.load_system_host_keys()
        connection.connect(
            ICP.get_param("account.invoice.efact.server", default=None),
            port=ICP.get_param("account.invoice.efact.port", default=None),
            username=ICP.get_param(
                "account.invoice.efact.user", default=None),
            password=ICP.get_param(
                "account.invoice.efact.password", default=None)
        )
        sftp = connection.open_sftp()
        return connection, sftp

    def get_filename(self, annex=''):
        invoice = self.integration_id.invoice_id
        filename = invoice.company_id.facturae_efact_code + '@'
        filename += invoice.partner_id.facturae_efact_code + '@'
        filename += invoice.number.replace('/', '_')
        if len(annex) > 0:
            filename += '@' + annex
        return filename

    def efact_transform_feedback(self, delivery_feedback, filename):
        hub_list = filename.rsplit('@', 1)
        hub_message_id = hub_list[1]
        for status in delivery_feedback.findall('StatusFeedback'):
            hub_feedback = status.find('HubFeedback')
            if hub_feedback is None:
                continue
            hub_reference = hub_feedback.find('HubFilename').text
            invoice_feedback = status.find('InvoiceFeedback')
            hub_id = hub_feedback.find('HubId').text
            if invoice_feedback is not None:
                integration = self.env['account.invoice.integration'].search([
                    ('method_id', '=', self.env.ref(
                        'l10n_es_facturae_efact.integration_efact').id),
                    ('efact_hub_id', '=', hub_id)
                ])
                if not integration:
                    integration = self.env[
                        'account.invoice.integration'
                    ].search([
                        ('method_id', '=', self.env.ref(
                            'l10n_es_facturae_efact.integration_efact').id),
                        ('efact_hub_id', '=', False),
                        ('efact_reference', '=', hub_reference)
                    ])
                    integration.efact_hub_id = hub_id
                for feedback in invoice_feedback.findall('Feedback'):
                    self.env['account.invoice.integration.log'].create({
                        'type': 'update',
                        'integration_id': integration.id,
                        'state': 'sent',
                        'log': feedback.find('Status').text,
                        'hub_message_id': hub_message_id,
                        'update_date': feedback.find('StatusDate').text
                    })
                    register = feedback.find('RegisterNumber')
                    if (
                        register is not None and
                        not integration.register_number
                    ):
                        integration.register_number = register.text
                    integration.integration_status = 'efact-' + feedback.find(
                        'Status').text
                    integration.integration_description = feedback.find(
                        'Reason'
                    ).find('Description').text
                for annex in feedback.findall('ElectronicAcknowledgment'):
                    annex_name = '%a.%s' % (
                        integration.register_number,
                        annex.find('formatType').text
                    )
                    self.env['ir.attachment'].create({
                        'name': annex_name,
                        'datas': annex.find('document').text,
                        'datas_fname': annex_name,
                        'res_model': 'account.invoice.integration',
                        'res_id': integration.id,
                        'mimetype': 'application/xml'
                    })
            else:
                integration = self.env['account.invoice.integration'].search([
                    ('method_id', '=', self.env.ref(
                        'l10n_es_facturae_efact.integration_efact').id),
                    ('efact_hub_id', '=', False),
                    ('efact_reference', '=', hub_reference)
                ])
                integration.efact_hub_id = hub_id
                self.env['account.invoice.integration.log'].create({
                    'type': 'update',
                    'integration_id': integration.id,
                    'state': 'sent',
                    'log': '%s - %s' % (
                        hub_feedback.find('HubStatus').text,
                        hub_feedback.find('HubErrorCode').text,
                    ),
                    'hub_message_id': hub_message_id,
                    'update_date': hub_feedback.find('HubStatusDate').text
                })

    def send_method(self):
        if self.integration_id.method_id == self.env.ref(
                'l10n_es_facturae_efact.integration_efact'):
            connection, sftp = self._efact_connect()
            try:
                path = sftp.normalize('.')
                sftp.chdir(path + in_path)
                file = sftp.open(self.get_filename(), 'wb')
                encoded = base64.b64decode(
                    self.integration_id.attachment_id.datas
                )
                file.write(encoded)
                file.flush()
                file.close()
                sftp.chdir(path + adjin_path)
                if self.integration_id.attachment_ids:
                    integer = 1
                    for attachment in self.integration_id.attachment_ids:
                        annex = sftp.open(
                            self.get_filename(
                                '%03d.%s' % (
                                    integer,
                                    attachment.name.split('.')[-1])
                            ),
                            'wb'
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
        path = sftp.normalize('.')
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
