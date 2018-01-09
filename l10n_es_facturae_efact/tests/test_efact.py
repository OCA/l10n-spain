# © 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo.tests import common
from odoo import exceptions, tools
from mock import patch
from datetime import datetime
import base64
import logging
from io import BytesIO
try:
    from OpenSSL import crypto
except (ImportError, IOError) as err:
    logging.info(err)


class TestL10nEsFacturae(common.TransactionCase):
    def setUp(self):
        super(TestL10nEsFacturae, self).setUp()
        pkcs12 = crypto.PKCS12()
        pkey = crypto.PKey()
        pkey.generate_key(crypto.TYPE_RSA, 512)
        x509 = crypto.X509()
        x509.set_pubkey(pkey)
        x509.set_serial_number(0)
        x509.get_subject().CN = "me"
        x509.set_issuer(x509.get_subject())
        x509.gmtime_adj_notBefore(0)
        x509.gmtime_adj_notAfter(10 * 365 * 24 * 60 * 60)
        x509.sign(pkey, 'md5')
        pkcs12.set_privatekey(pkey)
        pkcs12.set_certificate(x509)
        main_company = self.env.ref('base.main_company')
        main_company.facturae_cert = base64.b64encode(
            pkcs12.export(passphrase='password'))
        main_company.facturae_cert_password = 'password'
        self.tax = self.env['account.tax'].create({
            'name': 'Test tax',
            'amount_type': 'percent',
            'amount': 21,
            'type_tax_use': 'sale',
            'facturae_code': '01',
        })
        self.state = self.env['res.country.state'].create({
            'name': 'Ciudad Real',
            'code': '13',
            'country_id': self.ref('base.es'),
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Cliente de prueba',
            'street': 'C/ Ejemplo, 13',
            'zip': '13700',
            'city': 'Tomelloso',
            'state_id': self.state.id,
            'country_id': self.ref('base.es'),
            'vat': 'ES05680675C',
            'facturae': True,
            'organo_gestor': 'U00000038',
            'unidad_tramitadora': 'U00000038',
            'oficina_contable': 'U00000038',
            'facturae_efact_code': '012345678901234567',
            'invoice_integration_method_ids': [(6, 0, [
                self.env.ref('l10n_es_facturae_efact.integration_efact').id
            ])]
        })
        main_company.partner_id.facturae_efact_code = '012345678901234567'
        main_company.vat = "ESA12345674"
        main_company.partner_id.country_id = self.ref('base.uk')
        main_company.currency_id = self.ref('base.EUR')
        self.env['res.currency.rate'].search(
            [('currency_id', '=', main_company.currency_id.id)]
        ).write({'company_id': False})
        bank_obj = self.env['res.partner.bank']
        self.bank = bank_obj.search([
            ('acc_number', '=', 'BE96 9988 7766 5544')], limit=1)
        if not self.bank:
            self.bank = bank_obj.create({
                'state': 'iban',
                'acc_number': 'BE96 9988 7766 5544',
                'partner_id': self.partner.id,
                'bank_id': self.env['res.bank'].search(
                    [('bic', '=', 'PSSTFRPPXXX')], limit=1).id
            })
        self.mandate = self.env['account.banking.mandate'].create({
            'company_id': main_company.id,
            'format': 'basic',
            'partner_id': self.partner.id,
            'state': 'valid',
            'partner_bank_id': self.bank.id,
            'signature_date': '2016-03-12',
        })

        self.payment_method = self.env['account.payment.method'].create({
            'name': 'inbound_mandate',
            'code': 'inbound_mandate',
            'payment_type': 'inbound',
            'bank_account_required': False,
            'mandate_required': True,
            'active': True
        })
        payment_methods = self.env['account.payment.method'].search([
            ('payment_type', '=', 'inbound')
        ])
        self.journal = self.env['account.journal'].create({
            'name': 'Test journal',
            'code': 'TEST',
            'type': 'bank',
            'company_id': main_company.id,
            'inbound_payment_method_ids': [(6, 0, payment_methods.ids)]
        })
        self.payment_mode = self.env['account.payment.mode'].create({
            'name': 'Test payment mode',
            'bank_account_link': 'fixed',
            'fixed_journal_id': self.journal.id,
            'payment_method_id': self.env.ref(
                'payment.account_payment_method_electronic_in').id,
            'facturae_code': '01',
        })

        self.payment_mode_02 = self.env['account.payment.mode'].create({
            'name': 'Test payment mode 02',
            'bank_account_link': 'fixed',
            'fixed_journal_id': self.journal.id,
            'payment_method_id': self.payment_method.id,
            'facturae_code': '02',
        })

        account = self.env['account.account'].create({
            'company_id': main_company.id,
            'name': 'Facturae Product account',
            'code': 'facturae_product',
            'user_type_id': self.env.ref(
                'account.data_account_type_revenue').id
        })
        self.invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'account_id': self.partner.property_account_receivable_id.id,
            'journal_id': self.journal.id,
            'date_invoice': '2016-03-12',
            'partner_bank_id': self.bank.id,
            'payment_mode_id': self.payment_mode.id
        })
        self.invoice_line = self.env['account.invoice.line'].create({
            'product_id': self.env.ref('product.product_delivery_02').id,
            'account_id': account.id,
            'invoice_id': self.invoice.id,
            'name': 'Producto de prueba',
            'quantity': 1.0,
            'price_unit': 100.0,
            'invoice_line_tax_ids': [(6, 0, self.tax.ids)],
        })
        self.invoice._onchange_invoice_line_ids()
        self.invoice.action_invoice_open()
        self.invoice.number = 'R/0001'

    def test_efact_sending(self):
        class TestConnection:
            def __init__(self, data, filename=''):
                self.data = data
                self.filename = filename

            def connect(self, hostname, port, username, password):
                return

            def open_sftp(self):
                return SftpConnection(self.data, self.filename)

            def close(self):
                return

            def load_system_host_keys(self):
                return

            def get_host_keys(self):
                return Keys()

        class Keys:
            def add(self, *args):
                return

        class SftpConnection:
            def __init__(self, data, filename):
                self.data = data
                self.filename = filename

            def close(self):
                return

            def normalize(self, path):
                return path

            def chdir(self, path):
                return

            def open(self, path, type=''):
                return BytesIO(self.data)

            def listdir_attr(self, path):
                return [TestAttribute(self.filename)]

            def remove(self, filename):
                return

        class TestAttribute:
            def __init__(self, name):
                self.filename = name
                self.st_atime = datetime.now()

        patch_class = 'odoo.addons.l10n_es_facturae_efact.models.' \
                      'account_invoice_integration_log.SSHClient'
        self.invoice.action_integrations()
        integration = self.env['account.invoice.integration'].search([
            ('invoice_id', '=', self.invoice.id)
        ])
        self.assertEqual(integration.method_code, "eFACT")
        self.assertEqual(integration.can_send, True)
        attachment = self.env['ir.attachment'].create({
            'name': "attach.txt",
            'datas': base64.b64encode("attachment".encode('utf-8')),
            'datas_fname': "attach.txt",
            'res_model': 'account.invoice',
            'res_id': self.invoice.id,
            'mimetype': 'text/plain'
        })
        integration.attachment_ids = [(6, 0, attachment.ids)]
        with patch(patch_class) as mock:
            mock.return_value = TestConnection(bytes(''.encode('utf-8')))
            integration.send_action()
        self.assertEqual(integration.state, 'sent')
        with self.assertRaises(exceptions.UserError):
            integration.update_action()
        with self.assertRaises(exceptions.ValidationError):
            self.env['account.invoice.integration.cancel'].create({
                'integration_id': integration.id
            }).cancel_integration()
        with patch(patch_class) as mock:
            mock.return_value = TestConnection(
                bytes(tools.file_open(
                    'result.xml',
                    subdir="addons/l10n_es_facturae_efact/tests"
                ).read().encode('utf-8')),
                integration.efact_reference + '@001')
            self.env['account.invoice.integration.log'].efact_check_history()
        self.assertEqual(integration.efact_hub_id, '12')
