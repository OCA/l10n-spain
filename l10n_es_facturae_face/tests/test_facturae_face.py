# © 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64

from odoo import exceptions
from odoo.tests import common
import logging
import mock
try:
    from zeep import Client
    from OpenSSL import crypto
except (ImportError, IOError) as err:
    logging.info(err)


class TestL10nEsFacturaeFACe(common.TransactionCase):
    def setUp(self):
        super(TestL10nEsFacturaeFACe, self).setUp()
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
            'invoice_integration_method_ids': [(6, 0, [
                self.env.ref('l10n_es_facturae_face.integration_face').id
            ])]
        })
        main_company.vat = "ESA12345674"
        main_company.partner_id.country_id = self.ref('base.uk')
        self.env.cr.execute(
            "UPDATE res_company SET currency_id = %s",
            (self.ref('base.EUR'), ),
        )
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
        self.invoice.number = '2999/99998'

    def test_facturae_face(self):
        class DemoService(object):
            def __init__(self, value):
                self.value = value

            def enviarFactura(self, *args):
                return self.value

            def anularFactura(self, *args):
                return self.value

            def consultarFactura(self, *args):
                return self.value

        main_company = self.env.ref('base.main_company')
        with self.assertRaises(exceptions.ValidationError):
            main_company.face_email = 'test'
        main_company.face_email = 'test@test.com'
        self.invoice.action_integrations()
        integration = self.env['account.invoice.integration'].search([
            ('invoice_id', '=', self.invoice.id)
        ])
        self.assertEqual(integration.method_id.code, "FACe")
        self.assertEqual(integration.can_send, True)
        client = Client(
            wsdl=self.env["ir.config_parameter"].get_param(
                "account.invoice.face.server", default=None)
        )
        integration.send_action()
        self.assertEqual(integration.state, 'failed')
        integration_code = '1234567890'
        response_ok = client.get_type('ns0:EnviarFacturaResponse')(
            client.get_type('ns0:Resultado')(
                codigo='0',
                descripcion='OK'
            ),
            client.get_type('ns0:EnviarFactura')(
                numeroRegistro=integration_code
            )
        )
        with mock.patch('zeep.client.ServiceProxy') as mock_client:
            mock_client.return_value = DemoService(response_ok)
            integration.send_action()
        self.assertEqual(integration.register_number, integration_code)
        self.assertEqual(integration.state, 'sent')
        response_update = client.get_type('ns0:ConsultarFacturaResponse')(
            client.get_type('ns0:Resultado')(
                codigo='0',
                descripcion='OK'
            ),
            client.get_type('ns0:ConsultarFactura')(
                '1234567890',
                client.get_type('ns0:EstadoFactura')(
                    '1200',
                    'DESC',
                    'MOTIVO'
                ),
                client.get_type('ns0:EstadoFactura')(
                    '4100',
                    'DESC',
                    'MOTIVO'
                )
            )
        )
        with mock.patch('zeep.client.ServiceProxy') as mock_client:
            mock_client.return_value = DemoService(response_update)
            integration.update_action()
        self.assertEqual(integration.integration_status, 'face-1200')
        response_cancel = client.get_type('ns0:ConsultarFacturaResponse')(
            client.get_type('ns0:Resultado')(
                '0',
                'OK'
            ),
            client.get_type('ns0:AnularFactura')(
                '1234567890',
                'ANULADO'
            )
        )
        with mock.patch('zeep.client.ServiceProxy') as mock_client:
            mock_client.return_value = DemoService(response_cancel)
            cancel = self.env['account.invoice.integration.cancel'].create({
                'integration_id': integration.id,
                'motive': 'Anulacion'
            })
            cancel.cancel_integration()
        self.assertEqual(integration.state, 'cancelled')
