# Copyright 2021 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import datetime, timedelta

from odoo import exceptions
from odoo.tests.common import tagged
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT

from ..ticketbai.xml_schema import XMLSchema
from .common import TestL10nEsTicketBAIAPI


@tagged("post_install", "-at_install")
class TestL10nEsTicketBAIInvoice(TestL10nEsTicketBAIAPI):
    def setUp(self):
        super().setUp()

    def test_invoice(self):
        uid = self.tech_user.id
        invoice = self.create_tbai_national_invoice(
            name="TBAITEST/00001",
            company_id=self.main_company.id,
            number="00001",
            number_prefix="TBAITEST/",
            uid=uid,
        )
        self.assertEqual(invoice.state, "draft")
        self.add_customer_from_odoo_partner_to_invoice(invoice.id, self.partner)
        self.assertEqual(1, len(invoice.tbai_customer_ids))
        root, signature_value = invoice.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)

    def test_missing_customer_address(self):
        uid = self.tech_user.id
        invoice = self.create_tbai_national_invoice(
            name="TBAITEST/00001",
            company_id=self.main_company.id,
            number="00001",
            number_prefix="TBAITEST/",
            uid=uid,
        )
        self.assertEqual(invoice.state, "draft")
        self.env["tbai.invoice.customer"].create(
            {
                "tbai_invoice_id": invoice.id,
                "name": self.partner.tbai_get_value_apellidos_nombre_razon_social(),
                "country_code": self.partner.country_id.code.upper(),
                "nif": self.partner.tbai_get_value_nif(),
                "identification_number": self.partner.tbai_partner_identification_number
                or self.partner.vat,
                "idtype": self.partner.tbai_partner_idtype,
                "zip": self.partner.zip,
            }
        )
        self.assertEqual(1, len(invoice.tbai_customer_ids))
        with self.assertRaises(exceptions.ValidationError):
            invoice.get_tbai_xml_signed_and_signature_value()

    def test_missing_customer_zip(self):
        uid = self.tech_user.id
        invoice = self.create_tbai_national_invoice(
            name="TBAITEST/00001",
            company_id=self.main_company.id,
            number="00001",
            number_prefix="TBAITEST/",
            uid=uid,
        )
        self.assertEqual(invoice.state, "draft")
        self.env["tbai.invoice.customer"].create(
            {
                "tbai_invoice_id": invoice.id,
                "name": self.partner.tbai_get_value_apellidos_nombre_razon_social(),
                "country_code": self.partner.country_id.code.upper(),
                "nif": self.partner.tbai_get_value_nif(),
                "identification_number": self.partner.tbai_partner_identification_number
                or self.partner.vat,
                "idtype": self.partner.tbai_partner_idtype,
                "address": self.partner.tbai_get_value_direccion(),
            }
        )
        self.assertEqual(1, len(invoice.tbai_customer_ids))
        with self.assertRaises(exceptions.ValidationError):
            invoice.get_tbai_xml_signed_and_signature_value()

    def test_partner_missing_country_code(self):
        self.partner.country_id = False
        self.partner.vat = "B00000000"
        with self.assertRaises(exceptions.ValidationError):
            self.partner.tbai_get_partner_country_code()

    def test_qr_url(self):
        uid = self.tech_user.id
        qr_base_url = self.main_company.tbai_tax_agency_id.test_qr_base_url
        invoice = self.create_tbai_national_invoice(
            name="TBAITEST/00001",
            company_id=self.main_company.id,
            number="00001",
            number_prefix="TBAITEST/",
            uid=uid,
        )
        self.assertEqual(invoice.state, "draft")
        self.add_customer_from_odoo_partner_to_invoice(invoice.id, self.partner)
        invoice.build_tbai_invoice()
        self.assertEqual(qr_base_url, invoice.qr_url[: len(qr_base_url)])
        # Simulate new Tax Agency Version
        current_version = self.main_company.tbai_tax_agency_id.get_current_version()
        yesterday = (datetime.now() - timedelta(days=1)).strftime(
            DEFAULT_SERVER_DATE_FORMAT
        )
        current_version.date_to = yesterday
        version = self.env["tbai.tax.agency.version"].create(
            {
                "tbai_tax_agency_id": self.main_company.tbai_tax_agency_id.id,
                "version": "0.0",
                "qr_base_url": "https://qr-base-url.eus/",
                "test_qr_base_url": "https://test-qr-base-url.eus/",
                "test_rest_url_invoice": "",
                "test_rest_url_cancellation": "",
            }
        )
        qr_base_url = self.main_company.tbai_tax_agency_id.test_qr_base_url
        self.assertEqual(qr_base_url, version.test_qr_base_url)
        self.assertEqual(qr_base_url, invoice.qr_url[: len(qr_base_url)])

    def _prepare_invoice_send_to_tax_agency(self):
        uid = self.tech_user.id
        number = self.get_next_number()
        name = "%s%s" % (self.number_prefix, number)
        invoice = self.create_tbai_national_invoice(
            name=name,
            company_id=self.main_company.id,
            number=number,
            number_prefix=self.number_prefix,
            uid=uid,
        )
        self.add_customer_from_odoo_partner_to_invoice(invoice.id, self.partner)
        invoice.build_tbai_invoice()
        self._send_to_tax_agency(invoice)

    def test_invoice_send_to_tax_agency(self):
        if self.send_to_tax_agency:
            self._prepare_gipuzkoa_company(self.main_company)
            self._prepare_invoice_send_to_tax_agency()
            self._prepare_araba_company(self.main_company)
            self._prepare_invoice_send_to_tax_agency()

    def test_chaining_and_rejected_by_the_tax_agency(self):
        uid = self.tech_user.id
        # Build three invoices and check the chaining.
        invoice = self.create_tbai_national_invoice(
            name="TBAITEST/00001",
            company_id=self.main_company.id,
            number="00001",
            number_prefix="TBAITEST/",
            uid=uid,
        )
        self.assertEqual(invoice.state, "draft")
        self.add_customer_from_odoo_partner_to_invoice(invoice.id, self.partner)
        invoice.build_tbai_invoice()
        self.assertEqual(invoice.state, "pending")
        self.assertEqual(self.main_company.tbai_last_invoice_id, invoice)

        invoice2 = self.create_tbai_national_invoice(
            name="TBAITEST/00002",
            company_id=self.main_company.id,
            number="00002",
            number_prefix="TBAITEST/",
            uid=uid,
        )
        self.assertEqual(invoice2.state, "draft")
        self.add_customer_from_odoo_partner_to_invoice(invoice2.id, self.partner)
        invoice2.build_tbai_invoice()
        self.assertEqual(invoice2.state, "pending")
        self.assertEqual(invoice2.previous_tbai_invoice_id, invoice)
        self.assertEqual(self.main_company.tbai_last_invoice_id, invoice2)

        invoice3 = self.create_tbai_national_invoice(
            name="TBAITEST/00003",
            company_id=self.main_company.id,
            number="00003",
            number_prefix="TBAITEST/",
            uid=uid,
        )
        self.assertEqual(invoice3.state, "draft")
        self.add_customer_from_odoo_partner_to_invoice(invoice3.id, self.partner)
        invoice3.build_tbai_invoice()
        self.assertEqual(invoice3.state, "pending")
        self.assertEqual(invoice3.previous_tbai_invoice_id, invoice2)
        self.assertEqual(self.main_company.tbai_last_invoice_id, invoice3)

        # Simulate 1st invoice sent successfully.
        # 2nd rejected by the Tax Agency. Mark as an error.
        # 3rd mark as an error.
        invoice.mark_as_sent()
        self.env["tbai.invoice"].mark_chain_as_error(invoice2)
        self.assertEqual(invoice2.state, "error")
        self.assertEqual(invoice3.state, "error")
        self.assertEqual(self.main_company.tbai_last_invoice_id, invoice)

    def test_exempted_invoice(self):
        uid = self.tech_user.id
        invoice = self.create_tbai_national_invoice_exempted(
            name="TBAITEST/00001",
            company_id=self.main_company.id,
            number="00001",
            number_prefix="TBAITEST/",
            uid=uid,
        )
        self.assertEqual(invoice.state, "draft")
        self.add_customer_from_odoo_partner_to_invoice(invoice.id, self.partner)
        self.assertEqual(1, len(invoice.tbai_customer_ids))
        root, signature_value = invoice.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)

    def _prepare_exempted_invoice_send_to_tax_agency(self):
        uid = self.tech_user.id
        number = self.get_next_number()
        name = "%s%s" % (self.number_prefix, number)
        invoice = self.create_tbai_national_invoice_exempted(
            name=name,
            company_id=self.main_company.id,
            number=number,
            number_prefix=self.number_prefix,
            uid=uid,
        )
        self.add_customer_from_odoo_partner_to_invoice(invoice.id, self.partner)
        invoice.build_tbai_invoice()
        self._send_to_tax_agency(invoice)

    def test_exempted_invoice_send_to_tax_agency(self):
        if self.send_to_tax_agency:
            self._prepare_gipuzkoa_company(self.main_company)
            self._prepare_exempted_invoice_send_to_tax_agency()
            self._prepare_araba_company(self.main_company)
            self._prepare_exempted_invoice_send_to_tax_agency()

    def test_not_subject_to_invoice(self):
        uid = self.tech_user.id
        invoice = self.create_tbai_national_invoice_not_subject_to(
            name="TBAITEST/00001",
            company_id=self.main_company.id,
            number="00001",
            number_prefix="TBAITEST/",
            uid=uid,
        )
        self.assertEqual(invoice.state, "draft")
        self.add_customer_from_odoo_partner_to_invoice(invoice.id, self.partner)
        self.assertEqual(1, len(invoice.tbai_customer_ids))
        root, signature_value = invoice.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)

    def _prepare_not_subject_to_invoice_send_to_tax_agency(self):
        uid = self.tech_user.id
        number = self.get_next_number()
        name = "%s%s" % (self.number_prefix, number)
        invoice = self.create_tbai_national_invoice_not_subject_to(
            name=name,
            company_id=self.main_company.id,
            number=number,
            number_prefix=self.number_prefix,
            uid=uid,
        )
        self.add_customer_from_odoo_partner_to_invoice(invoice.id, self.partner)
        invoice.build_tbai_invoice()
        self._send_to_tax_agency(invoice)

    def test_not_subject_to_invoice_send_to_tax_agency(self):
        if self.send_to_tax_agency:
            self._prepare_gipuzkoa_company(self.main_company)
            self._prepare_not_subject_to_invoice_send_to_tax_agency()
            self._prepare_araba_company(self.main_company)
            self._prepare_not_subject_to_invoice_send_to_tax_agency()

    def test_invoice_foreign_customer_extracommunity(self):
        uid = self.tech_user.id
        invoice = self.create_tbai_extracommunity_invoice(
            name="TBAITEST/00001",
            company_id=self.main_company.id,
            number="00001",
            number_prefix="TBAITEST/",
            uid=uid,
        )
        self.assertEqual(invoice.state, "draft")
        self.add_customer_from_odoo_partner_to_invoice(
            invoice.id, self.partner_extracommunity
        )
        self.assertEqual(1, len(invoice.tbai_customer_ids))
        root, signature_value = invoice.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)

    def _prepare_invoice_foreign_customer_extracommunity_send_to_tax_agency(self):
        uid = self.tech_user.id
        number = self.get_next_number()
        name = "%s%s" % (self.number_prefix, number)
        invoice = self.create_tbai_extracommunity_invoice(
            name=name,
            company_id=self.main_company.id,
            number=number,
            number_prefix=self.number_prefix,
            uid=uid,
        )
        self.add_customer_from_odoo_partner_to_invoice(
            invoice.id, self.partner_extracommunity
        )
        invoice.build_tbai_invoice()
        self._send_to_tax_agency(invoice)

    def test_invoice_foreign_customer_extracommunity_send_to_tax_agency(self):
        if self.send_to_tax_agency:
            self._prepare_gipuzkoa_company(self.main_company)
            self._prepare_invoice_foreign_customer_extracommunity_send_to_tax_agency()
            self._prepare_araba_company(self.main_company)
            self._prepare_invoice_foreign_customer_extracommunity_send_to_tax_agency()

    def test_invoice_foreign_customer_intracommunity(self):
        uid = self.tech_user.id
        invoice = self.create_tbai_intracommunity_invoice(
            name="TBAITEST/00001",
            company_id=self.main_company.id,
            number="00001",
            number_prefix="TBAITEST/",
            uid=uid,
        )
        self.assertEqual(invoice.state, "draft")
        self.add_customer_from_odoo_partner_to_invoice(
            invoice.id, self.partner_intracommunity
        )
        self.assertEqual(1, len(invoice.tbai_customer_ids))
        root, signature_value = invoice.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)

    def _prepare_invoice_foreign_customer_intracommunity_send_to_tax_agency(self):
        uid = self.tech_user.id
        number = self.get_next_number()
        name = "%s%s" % (self.number_prefix, number)
        invoice = self.create_tbai_intracommunity_invoice(
            name=name,
            company_id=self.main_company.id,
            number=number,
            number_prefix=self.number_prefix,
            uid=uid,
        )
        self.add_customer_from_odoo_partner_to_invoice(
            invoice.id, self.partner_intracommunity
        )
        invoice.build_tbai_invoice()
        self._send_to_tax_agency(invoice)

    def test_invoice_foreign_customer_intracommunity_send_to_tax_agency(self):
        if self.send_to_tax_agency:
            self._prepare_gipuzkoa_company(self.main_company)
            self._prepare_invoice_foreign_customer_intracommunity_send_to_tax_agency()
            self._prepare_araba_company(self.main_company)
            self._prepare_invoice_foreign_customer_intracommunity_send_to_tax_agency()

    def test_invoice_irpf_taxes(self):
        uid = self.tech_user.id
        invoice = self.create_tbai_national_invoice_irpf(
            name="TBAITEST/00001",
            company_id=self.main_company.id,
            number="00001",
            number_prefix="TBAITEST/",
            uid=uid,
        )
        self.assertEqual(invoice.state, "draft")
        self.add_customer_from_odoo_partner_to_invoice(invoice.id, self.partner)
        self.assertEqual(1, len(invoice.tbai_customer_ids))
        root, signature_value = invoice.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)

    def _prepare_invoice_irpf_taxes_send_to_tax_agency(self):
        uid = self.tech_user.id
        number = self.get_next_number()
        name = "%s%s" % (self.number_prefix, number)
        invoice = self.create_tbai_national_invoice_irpf(
            name=name,
            company_id=self.main_company.id,
            number=number,
            number_prefix=self.number_prefix,
            uid=uid,
        )
        self.add_customer_from_odoo_partner_to_invoice(invoice.id, self.partner)
        invoice.build_tbai_invoice()
        self._send_to_tax_agency(invoice)

    def test_invoice_irpf_taxes_send_to_tax_agency(self):
        if self.send_to_tax_agency:
            self._prepare_gipuzkoa_company(self.main_company)
            self._prepare_invoice_irpf_taxes_send_to_tax_agency()
            self._prepare_araba_company(self.main_company)
            self._prepare_invoice_irpf_taxes_send_to_tax_agency()

    def test_invoice_equivalence_surcharge_taxes(self):
        uid = self.tech_user.id
        invoice = self.create_tbai_national_invoice_surcharge(
            name="TBAITEST/00001",
            company_id=self.main_company.id,
            number="00001",
            number_prefix="TBAITEST/",
            uid=uid,
        )
        self.assertEqual(invoice.state, "draft")
        self.add_customer_from_odoo_partner_to_invoice(invoice.id, self.partner)
        self.assertEqual(1, len(invoice.tbai_customer_ids))
        root, signature_value = invoice.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)

    def _prepare_invoice_equivalence_surcharge_taxes_send_to_tax_agency(self):
        uid = self.tech_user.id
        number = self.get_next_number()
        name = "%s%s" % (self.number_prefix, number)
        invoice = self.create_tbai_national_invoice_surcharge(
            name=name,
            company_id=self.main_company.id,
            number=number,
            number_prefix=self.number_prefix,
            uid=uid,
        )
        self.add_customer_from_odoo_partner_to_invoice(invoice.id, self.partner)
        invoice.build_tbai_invoice()
        self._send_to_tax_agency(invoice)

    def test_invoice_equivalence_surcharge_taxes_send_to_tax_agency(self):
        if self.send_to_tax_agency:
            self._prepare_gipuzkoa_company(self.main_company)
            self._prepare_invoice_equivalence_surcharge_taxes_send_to_tax_agency()
            self._prepare_araba_company(self.main_company)
            self._prepare_invoice_equivalence_surcharge_taxes_send_to_tax_agency()

    def test_invoice_refund(self):
        uid = self.tech_user.id
        # By differences
        refund_invoice_i = self.create_tbai_national_invoice_refund_by_differences(
            name="TBAITEST/REF/00001",
            company_id=self.main_company.id,
            number="00001",
            number_prefix="TBAITEST/REF/",
            uid=uid,
        )
        self.assertEqual(refund_invoice_i.state, "draft")
        self.add_customer_from_odoo_partner_to_invoice(
            refund_invoice_i.id, self.partner
        )
        self.assertEqual(1, len(refund_invoice_i.tbai_customer_ids))
        (
            root,
            signature_value,
        ) = refund_invoice_i.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)

        # By substitution
        refund_invoice_s = self.create_tbai_national_invoice_refund_by_substitution(
            name="TBAITEST/REF/00001",
            company_id=self.main_company.id,
            number="00001",
            number_prefix="TBAITEST/REF/",
            uid=uid,
        )
        self.assertEqual(refund_invoice_s.state, "draft")
        self.add_customer_from_odoo_partner_to_invoice(
            refund_invoice_s.id, self.partner
        )
        self.assertEqual(1, len(refund_invoice_s.tbai_customer_ids))
        (
            root,
            signature_value,
        ) = refund_invoice_s.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)

    def _prepare_invoice_refund_send_to_tax_agency_by_differences(self):
        uid = self.tech_user.id
        # First we need a registered Invoice to refund
        number = self.get_next_number()
        name = "%s%s" % (self.number_prefix, number)
        invoice = self.create_tbai_national_invoice(
            name=name,
            company_id=self.main_company.id,
            number=number,
            number_prefix=self.number_prefix,
            uid=uid,
        )
        self.add_customer_from_odoo_partner_to_invoice(invoice.id, self.partner)
        invoice.build_tbai_invoice()
        self._send_to_tax_agency(invoice)
        # By differences
        number = self.get_next_refund_number()
        name = "%s%s" % (self.refund_number_prefix, number)
        refund_invoice_i = self.create_tbai_national_invoice_refund_by_differences(
            name=name,
            company_id=self.main_company.id,
            number=number,
            number_prefix=self.refund_number_prefix,
            uid=uid,
        )
        self.add_customer_from_odoo_partner_to_invoice(
            refund_invoice_i.id, self.partner
        )
        refund_invoice_i.build_tbai_invoice()
        self._send_to_tax_agency(refund_invoice_i)

    def test_invoice_refund_send_to_tax_agency_by_differences(self):
        if self.send_to_tax_agency:
            self._prepare_gipuzkoa_company(self.main_company)
            self._prepare_invoice_refund_send_to_tax_agency_by_differences()
            self._prepare_araba_company(self.main_company)
            self._prepare_invoice_refund_send_to_tax_agency_by_differences()

    def _prepare_invoice_refund_send_to_tax_agency_by_substitution(self):
        uid = self.tech_user.id
        # First we need a registered Invoice to refund
        number = self.get_next_number()
        name = "%s%s" % (self.number_prefix, number)
        invoice = self.create_tbai_national_invoice(
            name=name,
            company_id=self.main_company.id,
            number=number,
            number_prefix=self.number_prefix,
            uid=uid,
        )
        self.add_customer_from_odoo_partner_to_invoice(invoice.id, self.partner)
        invoice.build_tbai_invoice()
        self._send_to_tax_agency(invoice)
        # By substitution
        number = self.get_next_refund_number()
        name = "%s%s" % (self.refund_number_prefix, number)
        refund_invoice_i = self.create_tbai_national_invoice_refund_by_substitution(
            name=name,
            company_id=self.main_company.id,
            number=number,
            number_prefix=self.refund_number_prefix,
            uid=uid,
        )
        self.add_customer_from_odoo_partner_to_invoice(
            refund_invoice_i.id, self.partner
        )
        refund_invoice_i.build_tbai_invoice()
        self._send_to_tax_agency(refund_invoice_i)

    def test_invoice_refund_send_to_tax_agency_by_substitution(self):
        if self.send_to_tax_agency:
            self._prepare_gipuzkoa_company(self.main_company)
            self._prepare_invoice_refund_send_to_tax_agency_by_substitution()
            self._prepare_araba_company(self.main_company)
            self._prepare_invoice_refund_send_to_tax_agency_by_substitution()
