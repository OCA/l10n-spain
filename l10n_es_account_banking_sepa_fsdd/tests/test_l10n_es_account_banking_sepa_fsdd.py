# Copyright 2017 Tecnativa S.L. - Luis M. Ontalba
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from lxml import etree
import base64

from odoo.tools import float_compare
from odoo.addons.account_banking_sepa_direct_debit.tests.test_sdd import \
    TestSDD


class TestSDD(TestSDD):

    def check_fsdd(self):
        self.mandate2.recurrent_sequence_type = 'first'
        invoice1 = self.create_invoice(
            self.partner_agrolait.id, self.mandate2, 42.0,
        )
        self.mandate12.type = 'oneoff'
        invoice2 = self.create_invoice(
            self.partner_c2c.id, self.mandate12, 11.0,
        )
        for inv in [invoice1, invoice2]:
            action = inv.create_account_payment_line()
        self.assertEqual(action['res_model'], 'account.payment.order')
        self.payment_order = self.payment_order_model.browse(action['res_id'])
        self.assertEqual(
            self.payment_order.payment_type, 'inbound')
        self.assertEqual(
            self.payment_order.payment_mode_id, self.payment_mode)
        self.assertEqual(
            self.payment_order.journal_id, self.bank_journal)
        # Check payment line
        pay_lines = self.payment_line_model.search([
            ('partner_id', '=', self.partner_agrolait.id),
            ('order_id', '=', self.payment_order.id)])
        self.assertEqual(len(pay_lines), 1)
        agrolait_pay_line1 = pay_lines[0]
        accpre = self.env['decimal.precision'].precision_get('Account')
        self.assertEqual(
            agrolait_pay_line1.currency_id, self.eur_currency)
        self.assertEqual(
            agrolait_pay_line1.mandate_id, invoice1.mandate_id)
        self.assertEqual(
            agrolait_pay_line1.partner_bank_id,
            invoice1.mandate_id.partner_bank_id)
        self.assertEqual(float_compare(
            agrolait_pay_line1.amount_currency, 42, precision_digits=accpre),
            0)
        self.assertEqual(agrolait_pay_line1.communication_type, 'normal')
        self.assertEqual(agrolait_pay_line1.communication, invoice1.number)
        self.payment_order.draft2open()
        self.assertEqual(self.payment_order.state, 'open')
        self.assertEqual(self.payment_order.sepa, True)
        # Check bank payment line
        bank_lines = self.bank_line_model.search([
            ('partner_id', '=', self.partner_agrolait.id)])
        self.assertEqual(len(bank_lines), 1)
        agrolait_bank_line = bank_lines[0]
        self.assertEqual(
            agrolait_bank_line.currency_id, self.eur_currency)
        self.assertEqual(float_compare(
            agrolait_bank_line.amount_currency, 42.0, precision_digits=accpre),
            0)
        self.assertEqual(agrolait_bank_line.communication_type, 'normal')
        self.assertEqual(
            agrolait_bank_line.communication, invoice1.number)
        self.assertEqual(
            agrolait_bank_line.mandate_id, invoice1.mandate_id)
        self.assertEqual(
            agrolait_bank_line.partner_bank_id,
            invoice1.mandate_id.partner_bank_id)
        action = self.payment_order.open2generated()
        self.assertEqual(self.payment_order.state, 'generated')
        self.assertEqual(action['res_model'], 'ir.attachment')
        attachment = self.attachment_model.browse(action['res_id'])
        self.assertEqual(attachment.datas_fname[-4:], '.xml')
        xml_file = base64.b64decode(attachment.datas)
        xml_root = etree.fromstring(xml_file)
        namespaces = xml_root.nsmap
        namespaces['p'] = xml_root.nsmap[None]
        namespaces.pop(None)
        pay_method_xpath = xml_root.xpath(
            '//p:PmtInf/p:PmtMtd', namespaces=namespaces)
        self.assertEqual(pay_method_xpath[0].text, 'DD')
        sepa_xpath = xml_root.xpath(
            '//p:PmtInf/p:PmtTpInf/p:SvcLvl/p:Cd', namespaces=namespaces)
        self.assertEqual(sepa_xpath[0].text, 'SEPA')
        debtor_acc_xpath = xml_root.xpath(
            '//p:PmtInf/p:CdtrAcct/p:Id/p:IBAN', namespaces=namespaces)
        self.assertEqual(
            debtor_acc_xpath[0].text,
            self.payment_order.company_partner_bank_id.sanitized_acc_number)
        self.payment_order.generated2uploaded()
        self.assertEqual(self.payment_order.state, 'uploaded')
        for inv in [invoice1, invoice2]:
            self.assertEqual(inv.state, 'paid')
        self.assertEqual(self.mandate2.recurrent_sequence_type, 'recurring')
        return

    def test_financed_sdd(self):
        self.payment_mode.charge_financed = True
        self.check_fsdd()
        self.mandate12.type = 'recurrent'
        self.mandate12.state = 'valid'
        self.mandate2.type = 'recurrent'
        self.mandate2.state = 'valid'
        action = self.payment_order.open2generated()
        attachment = self.attachment_model.browse(action['res_id'])
        xml_file = base64.b64decode(attachment.datas)
        xml_root = etree.fromstring(xml_file)
        namespaces = xml_root.nsmap
        namespaces['p'] = xml_root.nsmap[None]
        namespaces.pop(None)
        financed_sepa_xpath = xml_root.xpath('//p:GrpHdr/p:MsgId',
                                             namespaces=namespaces)
        self.assertEquals(financed_sepa_xpath[0].text[0:4], u"FSDD")
