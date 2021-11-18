# -*- encoding: utf-8 -*-

# Copyright 2021 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import date
from odoo import exceptions
from odoo.tests import common
from .common import TestL10nEsTicketBAI
from odoo.addons.l10n_es_ticketbai_api.ticketbai.xml_schema import XMLSchema


@common.at_install(False)
@common.post_install(True)
class TestL10nEsTicketBAICustomerInvoice(TestL10nEsTicketBAI):

    def setUp(self):
        super(TestL10nEsTicketBAICustomerInvoice, self).setUp()

    def test_invoice(self):
        invoice = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_national)
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice.compute_taxes()
        invoice.action_invoice_open()
        self.assertEqual(invoice.state, 'open')
        self.assertEqual(1, len(invoice.tbai_invoice_ids))
        root, signature_value = \
            invoice.sudo().tbai_invoice_ids.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)

    def test_cancel_and_recreate(self):
        # Build three invoices and check the chaining.
        invoice = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_national)
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice.compute_taxes()
        invoice.action_invoice_open()
        self.assertEqual(invoice.state, 'open')
        self.assertEqual(invoice.tbai_invoice_id.state, 'pending')
        self.assertEqual(
            self.main_company.tbai_last_invoice_id, invoice.tbai_invoice_id)

        invoice2 = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_national)
        invoice2.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice2.compute_taxes()
        invoice2.action_invoice_open()
        self.assertEqual(invoice2.state, 'open')
        self.assertEqual(invoice2.tbai_invoice_id.state, 'pending')
        self.assertEqual(
            self.main_company.tbai_last_invoice_id, invoice2.tbai_invoice_id)

        invoice3 = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_national)
        invoice3.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice3.compute_taxes()
        invoice3.action_invoice_open()
        self.assertEqual(invoice3.state, 'open')
        self.assertEqual(invoice3.tbai_invoice_id.state, 'pending')
        self.assertEqual(
            self.main_company.tbai_last_invoice_id, invoice3.tbai_invoice_id)

        # Simulate 1st invoice sent successfully.
        # 2nd rejected by the Tax Agency. Mark as an error.
        # 3rd mark as an error.
        invoice.tbai_invoice_id.sudo().mark_as_sent()
        self.env['tbai.invoice'].mark_chain_as_error(invoice2.sudo().tbai_invoice_id)
        self.assertEqual(invoice2.tbai_invoice_id.state, 'error')
        self.assertEqual(invoice3.tbai_invoice_id.state, 'error')
        self.assertEqual(
            self.main_company.tbai_last_invoice_id, invoice.tbai_invoice_id)

        # Cancel and recreate invoices with errors.
        with self.assertRaises(exceptions.ValidationError):
            invoice.tbai_invoice_id.cancel_and_recreate()
        invoices_with_errors = invoice2.tbai_invoice_id
        invoices_with_errors |= invoice3.tbai_invoice_id
        invoices_with_errors.cancel_and_recreate()
        self.assertEqual(invoices_with_errors[0].state, 'cancel')
        self.assertEqual(invoice2.tbai_invoice_id.state, 'pending')
        self.assertEqual(invoices_with_errors[1].state, 'cancel')
        self.assertEqual(invoice3.tbai_invoice_id.state, 'pending')

    def test_invoice_foreign_customer_extracommunity(self):
        invoice = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_e)
        invoice.partner_id = self.partner_extracommunity.id
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
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)

    def test_invoice_foreign_customer_intracommunity(self):
        invoice = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_ic)
        invoice.partner_id = self.partner_intracommunity.id
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
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)

    def test_invoice_irpf_taxes(self):
        invoice = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_irpf15)
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice.compute_taxes()
        invoice.action_invoice_open()
        self.assertEqual(invoice.state, 'open')
        self.assertEqual(1, len(invoice.tbai_invoice_ids))
        root, signature_value = \
            invoice.sudo().tbai_invoice_ids.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)

    def test_invoice_equivalence_surcharge_taxes(self):
        invoice = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_surcharge)
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice.compute_taxes()
        invoice.action_invoice_open()
        self.assertEqual(invoice.state, 'open')
        self.assertEqual(1, len(invoice.tbai_invoice_ids))
        root, signature_value = \
            invoice.sudo().tbai_invoice_ids.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)

    def test_out_refund_refund(self):
        invoice = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_national)
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice.compute_taxes()
        invoice.action_invoice_open()
        self.assertEqual(invoice.state, 'open')
        self.assertEqual(1, len(invoice.tbai_invoice_ids))
        root, signature_value = \
            invoice.sudo().tbai_invoice_ids.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
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
        invoice_refund = self.env['account.invoice'].search([('refund_invoice_id','=',invoice.id)])
        self.assertEqual(1, len(invoice_refund))
        self.assertEqual('I', invoice_refund.tbai_refund_type)
        self.assertEqual('R1', invoice_refund.tbai_refund_key)
        invoice_refund.compute_taxes()
        invoice_refund.action_invoice_open()
        self.assertEqual(invoice_refund.state, 'open')
        self.assertEqual(1, len(invoice_refund.tbai_invoice_ids))
        r_root, r_signature_value = \
            invoice_refund.sudo().tbai_invoice_ids.get_tbai_xml_signed_and_signature_value()
        r_res = XMLSchema.xml_is_valid(
            self.test_xml_invoice_schema_doc, r_root)
        self.assertTrue(r_res)

    def test_out_refund_refund_not_sent_invoice(self):
        self.main_company.tbai_enabled = False
        invoice = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_national)
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice.compute_taxes()
        invoice.action_invoice_open()
        self.assertEqual(invoice.state, 'open')
        self.assertEqual(0, len(invoice.tbai_invoice_ids))
        self.main_company.tbai_enabled = True
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
        invoice_refund = self.env['account.invoice'].search([('refund_invoice_id','=',invoice.id)])
        self.assertEqual(1, len(invoice_refund))
        self.assertEqual('I', invoice_refund.tbai_refund_type)
        self.assertEqual('R1', invoice_refund.tbai_refund_key)
        invoice_refund.compute_taxes()
        invoice_refund.action_invoice_open()
        self.assertEqual(invoice_refund.state, 'open')
        self.assertEqual(0, len(invoice_refund.tbai_invoice_ids))

    def test_out_refund_modify(self):
        invoice = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_national)
        invoice.origin = 'TBAI-REFUND-MODIFY-TEST'
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice.compute_taxes()
        invoice.action_invoice_open()
        self.assertEqual(invoice.state, 'open')
        self.assertEqual(1, len(invoice.tbai_invoice_ids))
        root, signature_value = \
            invoice.sudo().tbai_invoice_ids.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
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
        invoice_refund = self.env['account.invoice'].search([('refund_invoice_id','=',invoice.id)])
        self.assertEqual(1, len(invoice_refund))
        self.assertEqual(invoice_refund.state, 'paid')
        self.assertEqual('I', invoice_refund.tbai_refund_type)
        self.assertEqual('R1', invoice_refund.tbai_refund_key)
        self.assertEqual(1, len(invoice_refund.tbai_invoice_ids))
        invs = invoice_refund.sudo().tbai_invoice_ids
        r_root, r_signature_value = invs.get_tbai_xml_signed_and_signature_value()
        r_res = XMLSchema.xml_is_valid(
            self.test_xml_invoice_schema_doc, r_root)
        self.assertTrue(r_res)

    def test_out_refund_cancel(self):
        invoice = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_national)
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice.compute_taxes()
        invoice.action_invoice_open()
        self.assertEqual(invoice.state, 'open')
        self.assertEqual(1, len(invoice.tbai_invoice_ids))
        root, signature_value = \
            invoice.sudo().tbai_invoice_ids.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
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
        invoice_refund = self.env['account.invoice'].search([('refund_invoice_id','=',invoice.id)])
        self.assertEqual(1, len(invoice_refund))
        self.assertEqual('I', invoice_refund.tbai_refund_type)
        self.assertEqual('R1', invoice_refund.tbai_refund_key)
        self.assertEqual(invoice_refund.state, 'paid')
        self.assertEqual(1, len(invoice_refund.tbai_invoice_ids))
        r_root, r_signature_value = \
            invoice_refund.sudo().tbai_invoice_ids.get_tbai_xml_signed_and_signature_value()
        r_res = XMLSchema.xml_is_valid(
            self.test_xml_invoice_schema_doc, r_root)
        self.assertTrue(r_res)
    def test_invoice_line_iva_exento(self):
        invoice = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_national)
        product_iva_exento = self.create_product(
            product_name='Servicio Exento',
            product_type='service',
            product_taxes=[self.tax_iva0_exento_sujeto.id])
        invoice_line_obj = self.env['account.invoice.line'].sudo(
            self.account_billing.id
        ).create({
            'invoice_id': invoice.id,
            'product_id': product_iva_exento.id,
            'quantity': 1,
            'price_unit': 100.0,
            'name': 'TBAI Invoice Line Test - service IVA Exento',
            'account_id': self.account_revenue.id
        })
        invoice_line_obj._onchange_product_id()
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice.compute_taxes()
        invoice.action_invoice_open()
        self.assertEqual(invoice.state, 'open')
        self.assertEqual(1, len(invoice.tbai_invoice_ids))
        root, signature_value = \
            invoice.sudo().tbai_invoice_ids.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)
