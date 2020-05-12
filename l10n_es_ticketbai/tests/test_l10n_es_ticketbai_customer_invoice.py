# -*- coding: utf-8 -*-
# Copyright 2020 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import date
from odoo.tests import common
from .common import TestL10nEsTicketBAI
from ..ticketbai.xml_schema import XMLSchema


@common.at_install(False)
@common.post_install(True)
class TestL10nEsTicketBAICustomerInvoice(TestL10nEsTicketBAI):

    def setUp(self):
        super().setUp()

    def test_invoice(self):
        invoice = self.create_draft_invoice(self.account_billing.id,
                                            self.fiscal_position_national)
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice.compute_taxes()
        invoice.action_invoice_open()
        self.assertEqual(invoice.state, 'open')
        self.assertEqual(1, len(invoice.tbai_invoice_ids))
        root, signature_value = \
            invoice.sudo().tbai_invoice_ids.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_customer_invoice_schema_doc, root)
        self.assertTrue(res)

    def test_invoice_foreign_customer_extracommunity(self):
        invoice = self.create_draft_invoice(self.account_billing.id,
                                            self.fiscal_position_e)
        invoice.partner_id = self.customer_extracommunity.id
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice.compute_taxes()
        # Artículo 21.- Exenciones en las exportaciones de bienes
        self.assertEqual(invoice.tax_line_ids.filtered(
            lambda tax: tax.tax_id.id == self.tax_iva0_e.id
        ).tbai_vat_exemption_key, self.vat_exemption_E2)
        # Otros
        self.assertEqual(invoice.tax_line_ids.filtered(
            lambda tax: tax.tax_id.id == self.tax_iva0_sp_e.id
        ).tbai_vat_exemption_key, self.vat_exemption_E6)
        invoice.action_invoice_open()
        self.assertEqual(invoice.state, 'open')
        self.assertEqual(1, len(invoice.tbai_invoice_ids))
        root, signature_value = \
            invoice.sudo().tbai_invoice_ids.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_customer_invoice_schema_doc, root)
        self.assertTrue(res)

    def test_invoice_foreign_customer_intracommunity(self):
        invoice = self.create_draft_invoice(self.account_billing.id,
                                            self.fiscal_position_ic)
        invoice.partner_id = self.customer_intracommunity.id
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice.compute_taxes()
        # Artículo 25.- Exenciones en las entregas de bienes destinados a otro Estado
        # miembro
        self.assertTrue(all(
            tax.tbai_vat_exemption_key == self.vat_exemption_E5 for tax in
            invoice.tax_line_ids))
        invoice.action_invoice_open()
        self.assertEqual(invoice.state, 'open')
        self.assertEqual(1, len(invoice.tbai_invoice_ids))
        root, signature_value = \
            invoice.sudo().tbai_invoice_ids.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_customer_invoice_schema_doc, root)
        self.assertTrue(res)

    def test_invoice_irpf_taxes(self):
        invoice = self.create_draft_invoice(self.account_billing.id,
                                            self.fiscal_position_irpf15)
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice.compute_taxes()
        invoice.action_invoice_open()
        self.assertEqual(invoice.state, 'open')
        self.assertEqual(1, len(invoice.tbai_invoice_ids))
        root, signature_value = \
            invoice.sudo().tbai_invoice_ids.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_customer_invoice_schema_doc, root)
        self.assertTrue(res)

    def test_invoice_equivalence_surcharge_taxes(self):
        invoice = self.create_draft_invoice(self.account_billing.id,
                                            self.fiscal_position_surcharge)
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice.compute_taxes()
        invoice.action_invoice_open()
        self.assertEqual(invoice.state, 'open')
        self.assertEqual(1, len(invoice.tbai_invoice_ids))
        root, signature_value = \
            invoice.sudo().tbai_invoice_ids.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_customer_invoice_schema_doc, root)
        self.assertTrue(res)

    def test_out_refund_refund(self):
        invoice = self.create_draft_invoice(self.account_billing.id,
                                            self.fiscal_position_national)
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice.compute_taxes()
        invoice.action_invoice_open()
        self.assertEqual(invoice.state, 'open')
        self.assertEqual(1, len(invoice.tbai_invoice_ids))
        root, signature_value = \
            invoice.sudo().tbai_invoice_ids.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_customer_invoice_schema_doc, root)
        self.assertTrue(res)
        # Create an invoice refund by differences
        account_invoice_refund = \
            self.env['account.invoice.refund'].with_context(
                active_id=invoice.id,
                active_ids=invoice.ids
            ).create(dict(
                description='Credit Note for Binovo',
                date=date.today(),
                filter_refund='refund'
            ))
        account_invoice_refund.invoice_refund()
        self.assertEqual(1, len(invoice.refund_invoice_ids))
        refund = invoice.refund_invoice_ids
        self.assertEqual('I', refund.tbai_refund_type)
        self.assertEqual('R1', refund.tbai_refund_key)
        refund.compute_taxes()
        refund.action_invoice_open()
        self.assertEqual(refund.state, 'open')
        self.assertEqual(1, len(refund.tbai_invoice_ids))
        r_root, r_signature_value = \
            refund.sudo().tbai_invoice_ids.get_tbai_xml_signed_and_signature_value()
        r_res = XMLSchema.xml_is_valid(self.test_xml_customer_invoice_schema_doc,
                                       r_root)
        self.assertTrue(r_res)

    def test_out_refund_modify(self):
        invoice = self.create_draft_invoice(self.account_billing.id,
                                            self.fiscal_position_national)
        invoice.origin = 'TBAI-REFUND-MODIFY-TEST'
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice.compute_taxes()
        invoice.action_invoice_open()
        self.assertEqual(invoice.state, 'open')
        self.assertEqual(1, len(invoice.tbai_invoice_ids))
        root, signature_value = \
            invoice.sudo().tbai_invoice_ids.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_customer_invoice_schema_doc, root)
        self.assertTrue(res)
        # Create an invoice refund by substitution
        account_invoice_refund = \
            self.env['account.invoice.refund'].with_context(
                active_id=invoice.id,
                active_ids=invoice.ids
            ).create(dict(
                description='Credit Note for Binovo',
                date=date.today(),
                filter_refund='modify'
            ))
        account_invoice_refund.invoice_refund()
        self.assertEqual(1, len(invoice.refund_invoice_ids))
        refund = invoice.refund_invoice_ids
        self.assertEqual(refund.state, 'paid')
        substitute_invoice = self.env['account.invoice'].search([
            ('type', '=', 'out_invoice'), ('id', '!=', invoice.id),
            ('origin', '=', invoice.origin)
        ])
        self.assertEqual(1, len(substitute_invoice))
        self.assertEqual('S', substitute_invoice.tbai_refund_type)
        self.assertEqual('R1', substitute_invoice.tbai_refund_key)
        substitute_invoice.compute_taxes()
        substitute_invoice.action_invoice_open()
        self.assertEqual(substitute_invoice.state, 'open')
        self.assertEqual(1, len(substitute_invoice.tbai_invoice_ids))
        invs = substitute_invoice.sudo().tbai_invoice_ids
        r_root, r_signature_value = invs.get_tbai_xml_signed_and_signature_value()
        r_res = XMLSchema.xml_is_valid(
            self.test_xml_customer_invoice_schema_doc, r_root)
        self.assertTrue(r_res)

    def test_out_refund_cancel(self):
        invoice = self.create_draft_invoice(self.account_billing.id,
                                            self.fiscal_position_national)
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice.compute_taxes()
        invoice.action_invoice_open()
        self.assertEqual(invoice.state, 'open')
        self.assertEqual(1, len(invoice.tbai_invoice_ids))
        root, signature_value = \
            invoice.sudo().tbai_invoice_ids.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_customer_invoice_schema_doc, root)
        self.assertTrue(res)
        # Create an invoice refund by substitution
        account_invoice_refund = \
            self.env['account.invoice.refund'].with_context(
                active_id=invoice.id,
                active_ids=invoice.ids
            ).create(dict(
                description='Credit Note for Binovo',
                date=date.today(),
                filter_refund='cancel'
            ))
        account_invoice_refund.invoice_refund()
        self.assertEqual(1, len(invoice.refund_invoice_ids))
        refund = invoice.refund_invoice_ids
        self.assertEqual('I', refund.tbai_refund_type)
        self.assertEqual('R1', refund.tbai_refund_key)
        self.assertEqual(refund.state, 'paid')
        self.assertEqual(1, len(refund.tbai_invoice_ids))
        r_root, r_signature_value = \
            refund.sudo().tbai_invoice_ids.get_tbai_xml_signed_and_signature_value()
        r_res = XMLSchema.xml_is_valid(self.test_xml_customer_invoice_schema_doc,
                                       r_root)
        self.assertTrue(r_res)
