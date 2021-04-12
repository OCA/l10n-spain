# Copyright 2021 Binovo IT Human Project SL
# Copyright 2021 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import common
from .common import TestL10nEsTicketBAIAPI
from ..ticketbai.xml_schema import XMLSchema


@common.at_install(False)
@common.post_install(True)
class TestL10nEsTicketBAIInvoice(TestL10nEsTicketBAIAPI):

    def setUp(self):
        super().setUp()

    def test_invoice(self):
        uid = self.tech_user.id
        invoice = self.create_tbai_national_invoice(
            name='TBAITEST/00001', company_id=self.main_company.id, number='00001',
            number_prefix='TBAITEST/', uid=uid)
        self.assertEqual(invoice.state, 'draft')
        self.add_customer_from_odoo_partner_to_invoice(invoice.id, self.partner)
        self.assertEqual(1, len(invoice.tbai_customer_ids))
        root, signature_value = invoice.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)

    def test_invoice_send_to_tax_agency(self):
        if self.send_to_tax_agency:
            uid = self.tech_user.id
            number = self.get_next_number()
            name = "%s%s" % (self.number_prefix, number)
            invoice = self.create_tbai_national_invoice(
                name=name, company_id=self.main_company.id, number=number,
                number_prefix=self.number_prefix, uid=uid)
            self.add_customer_from_odoo_partner_to_invoice(invoice.id, self.partner)
            invoice.build_tbai_invoice()
            self._send_to_tax_agency(invoice)

    def test_invoice_cancel_and_recreate(self):
        uid = self.tech_user.id
        invoice = self.create_tbai_national_invoice(
            name='TBAITEST/00001', company_id=self.main_company.id, number='00001',
            number_prefix='TBAITEST/', uid=uid)
        self.assertEqual(invoice.state, 'draft')
        self.add_customer_from_odoo_partner_to_invoice(invoice.id, self.partner)
        invoice.build_tbai_invoice()
        self.assertEqual(invoice.state, 'pending')
        # Simulate successful request
        invoice.state = 'sent'
        # Create a second invoice
        invoice2 = self.create_tbai_national_invoice(
            name='TBAITEST/00002', company_id=self.main_company.id, number='00002',
            number_prefix='TBAITEST/', uid=uid)
        self.assertEqual(invoice2.state, 'draft')
        self.add_customer_from_odoo_partner_to_invoice(invoice2.id, self.partner)
        invoice2.build_tbai_invoice()
        self.assertEqual(invoice2.state, 'pending')
        # Create a third invoice
        invoice3 = self.create_tbai_national_invoice(
            name='TBAITEST/00003', company_id=self.main_company.id, number='00003',
            number_prefix='TBAITEST/', uid=uid)
        self.assertEqual(invoice3.state, 'draft')
        self.add_customer_from_odoo_partner_to_invoice(invoice3.id, self.partner)
        invoice3.build_tbai_invoice()
        self.assertEqual(invoice3.state, 'pending')
        # Simulate rejected request from the 2nd TicketBAI Invoice
        self.env['tbai.invoice'].cancel_and_recreate_pending_invoices(invoice2)
        self.assertEqual('cancel', invoice2.state)
        self.assertEqual('cancel', invoice3.state)
        new_inv2 = self.env['tbai.invoice'].search([
            ('state', '!=', 'cancel'),
            ('previous_tbai_invoice_id', '=', invoice.id)])
        self.assertEqual('pending', new_inv2.state)
        new_inv3 = self.env['tbai.invoice'].search([
            ('state', '!=', 'cancel'),
            ('previous_tbai_invoice_id', '=', new_inv2.id)])
        self.assertEqual('pending', new_inv3.state)

    def test_exempted_invoice(self):
        uid = self.tech_user.id
        invoice = self.create_tbai_national_invoice_exempted(
            name='TBAITEST/00001', company_id=self.main_company.id, number='00001',
            number_prefix='TBAITEST/', uid=uid)
        self.assertEqual(invoice.state, 'draft')
        self.add_customer_from_odoo_partner_to_invoice(invoice.id, self.partner)
        self.assertEqual(1, len(invoice.tbai_customer_ids))
        root, signature_value = invoice.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)

    def test_exempted_invoice_send_to_tax_agency(self):
        if self.send_to_tax_agency:
            uid = self.tech_user.id
            number = self.get_next_number()
            name = "%s%s" % (self.number_prefix, number)
            invoice = self.create_tbai_national_invoice_exempted(
                name=name, company_id=self.main_company.id, number=number,
                number_prefix=self.number_prefix, uid=uid)
            self.add_customer_from_odoo_partner_to_invoice(invoice.id, self.partner)
            invoice.build_tbai_invoice()
            self._send_to_tax_agency(invoice)

    def test_not_subject_to_invoice(self):
        uid = self.tech_user.id
        invoice = self.create_tbai_national_invoice_not_subject_to(
            name='TBAITEST/00001', company_id=self.main_company.id, number='00001',
            number_prefix='TBAITEST/', uid=uid)
        self.assertEqual(invoice.state, 'draft')
        self.add_customer_from_odoo_partner_to_invoice(invoice.id, self.partner)
        self.assertEqual(1, len(invoice.tbai_customer_ids))
        root, signature_value = invoice.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)

    def test_not_subject_to_invoice_send_to_tax_agency(self):
        if self.send_to_tax_agency:
            uid = self.tech_user.id
            number = self.get_next_number()
            name = "%s%s" % (self.number_prefix, number)
            invoice = self.create_tbai_national_invoice_not_subject_to(
                name=name, company_id=self.main_company.id, number=number,
                number_prefix=self.number_prefix, uid=uid)
            self.add_customer_from_odoo_partner_to_invoice(invoice.id, self.partner)
            invoice.build_tbai_invoice()
            self._send_to_tax_agency(invoice)

    def test_invoice_foreign_customer_extracommunity(self):
        uid = self.tech_user.id
        invoice = self.create_tbai_extracommunity_invoice(
            name='TBAITEST/00001', company_id=self.main_company.id, number='00001',
            number_prefix='TBAITEST/', uid=uid)
        self.assertEqual(invoice.state, 'draft')
        self.add_customer_from_odoo_partner_to_invoice(
            invoice.id, self.partner_extracommunity)
        self.assertEqual(1, len(invoice.tbai_customer_ids))
        root, signature_value = invoice.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)

    def test_invoice_foreign_customer_extracommunity_send_to_tax_agency(self):
        if self.send_to_tax_agency:
            uid = self.tech_user.id
            number = self.get_next_number()
            name = "%s%s" % (self.number_prefix, number)
            invoice = self.create_tbai_extracommunity_invoice(
                name=name, company_id=self.main_company.id, number=number,
                number_prefix=self.number_prefix, uid=uid)
            self.add_customer_from_odoo_partner_to_invoice(
                invoice.id, self.partner_extracommunity)
            invoice.build_tbai_invoice()
            self._send_to_tax_agency(invoice)

    def test_invoice_foreign_customer_intracommunity(self):
        uid = self.tech_user.id
        invoice = self.create_tbai_intracommunity_invoice(
            name='TBAITEST/00001', company_id=self.main_company.id, number='00001',
            number_prefix='TBAITEST/', uid=uid)
        self.assertEqual(invoice.state, 'draft')
        self.add_customer_from_odoo_partner_to_invoice(
            invoice.id, self.partner_intracommunity)
        self.assertEqual(1, len(invoice.tbai_customer_ids))
        root, signature_value = invoice.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)

    def test_invoice_foreign_customer_intracommunity_send_to_tax_agency(self):
        if self.send_to_tax_agency:
            uid = self.tech_user.id
            number = self.get_next_number()
            name = "%s%s" % (self.number_prefix, number)
            invoice = self.create_tbai_intracommunity_invoice(
                name=name, company_id=self.main_company.id, number=number,
                number_prefix=self.number_prefix, uid=uid)
            self.add_customer_from_odoo_partner_to_invoice(
                invoice.id, self.partner_intracommunity)
            invoice.build_tbai_invoice()
            self._send_to_tax_agency(invoice)

    def test_invoice_irpf_taxes(self):
        uid = self.tech_user.id
        invoice = self.create_tbai_national_invoice_irpf(
            name='TBAITEST/00001', company_id=self.main_company.id, number='00001',
            number_prefix='TBAITEST/', uid=uid)
        self.assertEqual(invoice.state, 'draft')
        self.add_customer_from_odoo_partner_to_invoice(invoice.id, self.partner)
        self.assertEqual(1, len(invoice.tbai_customer_ids))
        root, signature_value = invoice.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)

    def test_invoice_irpf_taxes_send_to_tax_agency(self):
        if self.send_to_tax_agency:
            uid = self.tech_user.id
            number = self.get_next_number()
            name = "%s%s" % (self.number_prefix, number)
            invoice = self.create_tbai_national_invoice_irpf(
                name=name, company_id=self.main_company.id, number=number,
                number_prefix=self.number_prefix, uid=uid)
            self.add_customer_from_odoo_partner_to_invoice(invoice.id, self.partner)
            invoice.build_tbai_invoice()
            self._send_to_tax_agency(invoice)

    def test_invoice_equivalence_surcharge_taxes(self):
        uid = self.tech_user.id
        invoice = self.create_tbai_national_invoice_surcharge(
            name='TBAITEST/00001', company_id=self.main_company.id, number='00001',
            number_prefix='TBAITEST/', uid=uid)
        self.assertEqual(invoice.state, 'draft')
        self.add_customer_from_odoo_partner_to_invoice(invoice.id, self.partner)
        self.assertEqual(1, len(invoice.tbai_customer_ids))
        root, signature_value = invoice.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)

    def test_invoice_equivalence_surcharge_taxes_send_to_tax_agency(self):
        if self.send_to_tax_agency:
            uid = self.tech_user.id
            number = self.get_next_number()
            name = "%s%s" % (self.number_prefix, number)
            invoice = self.create_tbai_national_invoice_surcharge(
                name=name, company_id=self.main_company.id, number=number,
                number_prefix=self.number_prefix, uid=uid)
            self.add_customer_from_odoo_partner_to_invoice(invoice.id, self.partner)
            invoice.build_tbai_invoice()
            self._send_to_tax_agency(invoice)

    def test_invoice_refund(self):
        uid = self.tech_user.id
        # By differences
        refund_invoice_i = self.create_tbai_national_invoice_refund_by_differences(
            name='TBAITEST/REF/00001', company_id=self.main_company.id, number='00001',
            number_prefix='TBAITEST/REF/', uid=uid)
        self.assertEqual(refund_invoice_i.state, 'draft')
        self.add_customer_from_odoo_partner_to_invoice(
            refund_invoice_i.id, self.partner)
        self.assertEqual(1, len(refund_invoice_i.tbai_customer_ids))
        root, signature_value = \
            refund_invoice_i.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)

        # By substitution
        refund_invoice_s = self.create_tbai_national_invoice_refund_by_substitution(
            name='TBAITEST/REF/00001', company_id=self.main_company.id, number='00001',
            number_prefix='TBAITEST/REF/', uid=uid)
        self.assertEqual(refund_invoice_s.state, 'draft')
        self.add_customer_from_odoo_partner_to_invoice(
            refund_invoice_s.id, self.partner)
        self.assertEqual(1, len(refund_invoice_s.tbai_customer_ids))
        root, signature_value = \
            refund_invoice_s.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)

    def test_invoice_refund_send_to_tax_agency_by_differences(self):
        if self.send_to_tax_agency:
            uid = self.tech_user.id
            # First we need a registered Invoice to refund
            number = self.get_next_number()
            name = "%s%s" % (self.number_prefix, number)
            invoice = self.create_tbai_national_invoice(
                name=name, company_id=self.main_company.id, number=number,
                number_prefix=self.number_prefix, uid=uid)
            self.add_customer_from_odoo_partner_to_invoice(invoice.id, self.partner)
            invoice.build_tbai_invoice()
            self._send_to_tax_agency(invoice)
            # By differences
            number = self.get_next_refund_number()
            name = "%s%s" % (self.refund_number_prefix, number)
            refund_invoice_i = self.create_tbai_national_invoice_refund_by_differences(
                name=name, company_id=self.main_company.id, number=number,
                number_prefix=self.refund_number_prefix, uid=uid)
            self.add_customer_from_odoo_partner_to_invoice(
                refund_invoice_i.id, self.partner)
            refund_invoice_i.build_tbai_invoice()
            self._send_to_tax_agency(refund_invoice_i)

    def test_invoice_refund_send_to_tax_agency_by_substitution(self):
        if self.send_to_tax_agency:
            uid = self.tech_user.id
            # First we need a registered Invoice to refund
            number = self.get_next_number()
            name = "%s%s" % (self.number_prefix, number)
            invoice = self.create_tbai_national_invoice(
                name=name, company_id=self.main_company.id, number=number,
                number_prefix=self.number_prefix, uid=uid)
            self.add_customer_from_odoo_partner_to_invoice(invoice.id, self.partner)
            invoice.build_tbai_invoice()
            self._send_to_tax_agency(invoice)
            # By substitution
            number = self.get_next_refund_number()
            name = "%s%s" % (self.refund_number_prefix, number)
            refund_invoice_i = self.create_tbai_national_invoice_refund_by_substitution(
                name=name, company_id=self.main_company.id, number=number,
                number_prefix=self.refund_number_prefix, uid=uid)
            self.add_customer_from_odoo_partner_to_invoice(
                refund_invoice_i.id, self.partner)
            refund_invoice_i.build_tbai_invoice()
            self._send_to_tax_agency(refund_invoice_i)
