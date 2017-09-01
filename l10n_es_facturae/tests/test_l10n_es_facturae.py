# -*- coding: utf-8 -*-
# © 2016 Serv. Tecnol. Avanzados - Pedro M. Baeza
# © 2017 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64

from lxml import etree
from odoo import exceptions
from odoo.tests import common
from OpenSSL import crypto


class TestL10nEsFacturae(common.TransactionCase):
    def setUp(self):
        super(TestL10nEsFacturae, self).setUp()
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
                self.env.ref('l10n_es_facturae.integration_demo').id
            ])]
        })
        main_company = self.env.ref('base.main_company')
        main_company.vat = "ESA12345674"
        main_company.partner_id.country_id = self.ref('base.uk')
        main_company.currency_id = self.ref('base.USD')
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
        self.invoice_02 = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'account_id': self.partner.property_account_receivable_id.id,
            'journal_id': self.journal.id,
            'date_invoice': '2016-03-12',
            'partner_bank_id': self.bank.id,
            'payment_mode_id': self.payment_mode_02.id,
            'mandate_id': self.mandate.id
        })

        self.invoice_line_02 = self.env['account.invoice.line'].create({
            'product_id': self.env.ref('product.product_delivery_02').id,
            'account_id': account.id,
            'invoice_id': self.invoice_02.id,
            'name': 'Producto de prueba',
            'quantity': 1.0,
            'price_unit': 100.0,
            'invoice_line_tax_ids': [(6, 0, self.tax.ids)],
        })
        self.invoice_02._onchange_invoice_line_ids()

    def test_facturae_generation(self):
        main_partner = self.partner
        main_partner.vat = 'ES05680675C'
        main_partner.is_company = False
        main_partner.firstname = 'Cliente'
        main_partner.lastname = "de Prueba"
        main_partner.country_id = self.ref('base.us'),
        main_partner.state_id = self.ref('base.state_us_2')
        self.invoice.action_invoice_open()
        self.invoice.number = '2999/99999'
        wizard = self.env['create.facturae'].create({})
        wizard.with_context(
            active_ids=self.invoice.ids).create_facturae_file()
        generated_facturae = etree.fromstring(
            base64.b64decode(wizard.facturae))
        fe = 'http://www.facturae.es/Facturae/2009/v3.2/Facturae'
        self.assertEqual(
            generated_facturae.xpath(
                '/fe:Facturae/Parties/SellerParty/TaxIdentification/'
                'TaxIdentificationNumber', namespaces={'fe': fe})[0].text,
            self.env.ref('base.main_company').vat
        )
        self.assertEqual(
            generated_facturae.xpath(
                '/fe:Facturae/Invoices/Invoice/InvoiceHeader/InvoiceNumber',
                namespaces={'fe': fe})[0].text,
            self.invoice.number
        )
        main_company = self.env.ref('base.main_company')
        self.bank.bank_id.bic = "CAIXESBB"
        with self.assertRaises(exceptions.ValidationError):
            self.invoice.validate_facturae_fields()
        with self.assertRaises(exceptions.ValidationError):
            self.invoice_02.validate_facturae_fields()
        self.bank.bank_id.bic = "CAIXESBBXXX"
        self.bank.acc_number = "1111"
        with self.assertRaises(exceptions.ValidationError):
            self.invoice.validate_facturae_fields()
        with self.assertRaises(exceptions.ValidationError):
            self.invoice_02.validate_facturae_fields()
        self.bank.acc_number = "BE96 9988 7766 5544"
        main_company.partner_id.country_id = False
        with self.assertRaises(exceptions.UserError):
            wizard.with_context(
                active_ids=self.invoice.ids).create_facturae_file()
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

        main_company.facturae_cert = base64.b64encode(
            pkcs12.export(passphrase='password'))
        main_company.facturae_cert_password = 'password'
        main_company.partner_id.country_id = self.ref('base.es')
        wizard.with_context(
            active_ids=self.invoice.ids).create_facturae_file()
        generated_facturae = etree.fromstring(
            base64.b64decode(wizard.facturae))
        ns = 'http://www.w3.org/2000/09/xmldsig#'
        self.assertEqual(len(generated_facturae.xpath('//ds:Signature',
                                                      namespaces={'ds': ns})),
                         1)
        motive = 'Description motive'
        refund = self.env['account.invoice.refund'].create(
            {'refund_reason': '01',
             'description': motive})
        refund_result = refund.with_context(
            active_ids=self.invoice.ids).invoice_refund()
        refund_inv = self.env['account.invoice'].search(
            refund_result['domain'])
        self.assertEquals(refund_inv.name, motive)
        self.assertEquals(refund_inv.refund_reason, '01')
        refund_inv.partner_bank_id = self.bank
        refund_inv.action_invoice_open()
        refund_inv.number = '2998/99999'
        wizard.with_context(active_ids=refund_inv.ids).create_facturae_file()
        with self.assertRaises(exceptions.UserError):
            wizard.with_context(active_ids=[
                self.invoice_02.id, self.invoice.id
            ]).create_facturae_file()
        self.assertTrue(self.invoice.can_integrate)
        self.assertEqual(self.invoice.integration_count, 0)
        integrations = self.invoice.action_integrations()
        self.assertEqual(self.invoice.integration_count, 1)
        integration = self.env['account.invoice.integration'].browse(
            integrations['res_id'])
        self.assertTrue(integration.can_send)
        integration.send_action()
        self.assertFalse(integration.can_send)
        self.assertTrue(integration.can_update)
        integration.update_action()
        self.assertTrue(integration.can_update)
        self.assertTrue(integration.can_cancel)
        self.env['account.invoice.integration.cancel'].create({
            'integration_id': integration.id
        }).cancel_integration()
        self.assertFalse(integration.can_cancel)
