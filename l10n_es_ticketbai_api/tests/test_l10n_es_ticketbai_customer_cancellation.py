# Copyright 2021 Binovo IT Human Project SL
# Copyright 2021 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests.common import tagged

from ..ticketbai.xml_schema import XMLSchema
from .common import TestL10nEsTicketBAIAPI


@tagged("post_install", "-at_install")
class TestL10nEsTicketBAICancellation(TestL10nEsTicketBAIAPI):
    def setUp(self):
        super().setUp()

    def test_invoice_cancel(self):
        uid = self.tech_user.id
        invoice = self.create_tbai_national_invoice_cancellation(
            name="TBAITEST/00001",
            company_id=self.main_company.id,
            number="00001",
            number_prefix="TBAITEST/",
            uid=uid,
        )
        self.assertEqual(invoice.state, "draft")
        root, signature_value = invoice.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_cancellation_schema_doc, root)
        self.assertTrue(res)

    def _prepare_invoice_cancel_send_to_tax_agency(self):
        uid = self.tech_user.id
        # First we need a registered (send to the Tax Agency) Invoice to Cancel
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
        pending_invoices = self.env["tbai.invoice"].get_next_pending_invoice(
            company_id=self.main_company.id, limit=0
        )
        self.assertEqual(1, len(pending_invoices))
        self.env["tbai.invoice"].send_pending_invoices()
        self.assertEqual("sent", invoice.state)
        pending_invoices = self.env["tbai.invoice"].get_next_pending_invoice(
            company_id=self.main_company.id, limit=0
        )
        self.assertEqual(0, len(pending_invoices))
        cancellation = self.create_tbai_national_invoice_cancellation(
            name=name,
            company_id=self.main_company.id,
            number=number,
            number_prefix=self.number_prefix,
            uid=uid,
        )
        cancellation.build_tbai_invoice()
        pending_invoices = self.env["tbai.invoice"].get_next_pending_invoice(
            company_id=self.main_company.id, limit=0
        )
        self.assertEqual(1, len(pending_invoices))
        self.env["tbai.invoice"].send_pending_invoices()
        self.assertEqual("sent", cancellation.state)
        pending_invoices = self.env["tbai.invoice"].get_next_pending_invoice(
            company_id=self.main_company.id, limit=0
        )
        self.assertEqual(0, len(pending_invoices))
        invoice.sudo().unlink()
        cancellation.sudo().unlink()

    def test_invoice_cancel_send_to_tax_agency(self):
        if self.send_to_tax_agency:
            self._prepare_gipuzkoa_company(self.main_company)
            self._prepare_invoice_cancel_send_to_tax_agency()
            self._prepare_araba_company(self.main_company)
            self._prepare_invoice_cancel_send_to_tax_agency()
