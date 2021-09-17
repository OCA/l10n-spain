# Copyright 2021 Binovo IT Human Project SL
# Copyright 2021 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import date

from odoo import exceptions
from odoo.tests.common import tagged

from odoo.addons.l10n_es_ticketbai_api.ticketbai.xml_schema import XMLSchema

from .common import TestL10nEsTicketBAI


@tagged("post_install", "-at_install")
class TestL10nEsTicketBAICustomerInvoice(TestL10nEsTicketBAI):
    def setUp(self):
        super().setUp()

    def test_invoice(self):
        invoice = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_national, self.partner
        )
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")
        self.assertEqual(1, len(invoice.tbai_invoice_ids))
        (
            root,
            signature_value,
        ) = invoice.sudo().tbai_invoice_ids.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)

    def test_resequence_customer(self):
        self.main_company.tbai_enabled = True
        invoice = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_national, self.partner
        )
        invoice_name = "INV/2021/0001"
        resequence_wizard = (
            self.env["account.resequence.wizard"]
            .with_context(active_model="account.move", active_ids=[invoice.id])
            .sudo()
            .create({"move_ids": [invoice.id], "first_name": invoice_name})
        )
        with self.assertRaises(exceptions.UserError):
            resequence_wizard.resequence()
        self.main_company.tbai_enabled = False
        resequence_wizard.resequence()

    def test_invoice_foreign_currency(self):
        invoice = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_national, self.partner
        )
        invoice.currency_id = self.env.ref("base.USD")
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")
        self.assertEqual(1, len(invoice.tbai_invoice_ids))
        (
            root,
            signature_value,
        ) = invoice.sudo().tbai_invoice_ids.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)

    def test_cancel_and_recreate(self):
        # Build three invoices and check the chaining.
        invoice = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_national, self.partner
        )
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")
        self.assertEqual(invoice.tbai_invoice_id.state, "pending")
        self.assertEqual(
            self.main_company.tbai_last_invoice_id, invoice.tbai_invoice_id
        )

        invoice2 = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_national, self.partner
        )
        invoice2.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice2.action_post()
        self.assertEqual(invoice2.state, "posted")
        self.assertEqual(invoice2.tbai_invoice_id.state, "pending")
        self.assertEqual(
            self.main_company.tbai_last_invoice_id, invoice2.tbai_invoice_id
        )

        invoice3 = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_national, self.partner
        )
        invoice3.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice3.action_post()
        self.assertEqual(invoice3.state, "posted")
        self.assertEqual(invoice3.tbai_invoice_id.state, "pending")
        self.assertEqual(
            self.main_company.tbai_last_invoice_id, invoice3.tbai_invoice_id
        )

        # Simulate 1st invoice sent successfully.
        # 2nd rejected by the Tax Agency. Mark as an error.
        # 3rd mark as an error.
        invoice.tbai_invoice_id.sudo().mark_as_sent()
        self.env["tbai.invoice"].mark_chain_as_error(invoice2.sudo().tbai_invoice_id)
        self.assertEqual(invoice2.tbai_invoice_id.state, "error")
        self.assertEqual(invoice3.tbai_invoice_id.state, "error")
        self.assertEqual(
            self.main_company.tbai_last_invoice_id, invoice.tbai_invoice_id
        )

        # Cancel and recreate invoices with errors.
        with self.assertRaises(exceptions.ValidationError):
            invoice.tbai_invoice_id.cancel_and_recreate()
        invoices_with_errors = invoice2.tbai_invoice_id
        invoices_with_errors |= invoice3.tbai_invoice_id
        invoices_with_errors.cancel_and_recreate()
        self.assertEqual(invoices_with_errors[0].state, "cancel")
        self.assertEqual(invoice2.tbai_invoice_id.state, "pending")
        self.assertEqual(invoices_with_errors[1].state, "cancel")
        self.assertEqual(invoice3.tbai_invoice_id.state, "pending")

    def test_invoice_ipsi_igic(self):
        invoice = self.create_draft_invoice(
            self.account_billing.id,
            self.fiscal_position_ipsi_igic,
            self.partner_extracommunity.id,
            only_service=True,
        )
        invoice.fiscal_position_id = invoice.company_id.get_fps_from_templates(
            self.env.ref("l10n_es.fp_not_subject_tai")
        )
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        self.assertEqual(1, len(invoice.invoice_line_ids))
        self.partner_extracommunity.country_id = self.env.ref("base.es").id
        for tax in invoice.invoice_line_ids.filtered(lambda x: x.tax_ids).mapped(
            "tax_ids"
        ):
            self.assertEqual("RL", tax.tbai_get_value_causa(invoice))
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")
        self.assertEqual(1, len(invoice.tbai_invoice_ids))
        (
            root,
            signature_value,
        ) = invoice.sudo().tbai_invoice_ids.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)
        self.partner_extracommunity.country_id = self.env.ref("base.jp").id

    def test_invoice_foreign_customer_extracommunity(self):
        invoice = self.create_draft_invoice(
            self.account_billing.id,
            self.fiscal_position_e,
            self.partner_extracommunity.id,
        )
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        # Artículo 21.- Exenciones en las exportaciones de bienes
        tax = invoice.invoice_line_ids.filtered(
            lambda line: any([t.id == self.tax_iva0_e.id for t in line.tax_ids])
        ).mapped("tax_ids")

        fp_tbai_tax = self.env["account.fp.tbai.tax"].search(
            [("tax_id", "=", tax.id), ("position_id", "=", self.fiscal_position_e.id)],
            limit=1,
        )

        self.assertEqual(
            fp_tbai_tax.tbai_vat_exemption_key,
            self.vat_exemption_E2,
        )
        # Otros
        tax = invoice.invoice_line_ids.filtered(
            lambda line: any([t.id == self.tax_iva0_sp_e.id for t in line.tax_ids])
        ).mapped("tax_ids")

        fp_tbai_tax = self.env["account.fp.tbai.tax"].search(
            [("tax_id", "=", tax.id), ("position_id", "=", self.fiscal_position_e.id)],
            limit=1,
        )

        self.assertEqual(
            fp_tbai_tax.tbai_vat_exemption_key,
            self.vat_exemption_E6,
        )

        invoice.action_post()
        self.assertEqual(invoice.state, "posted")
        self.assertEqual(1, len(invoice.tbai_invoice_ids))
        (
            root,
            signature_value,
        ) = invoice.sudo().tbai_invoice_ids.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)

    def test_invoice_foreign_customer_intracommunity(self):
        invoice = self.create_draft_invoice(
            self.account_billing.id,
            self.fiscal_position_ic,
            self.partner_intracommunity.id,
        )
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        # Artículo 25.- Exenciones en las entregas de bienes destinados a otro Estado
        # miembro
        self.assertTrue(
            all(
                tax.tbai_vat_exemption_key == self.vat_exemption_E5
                for tax in invoice.line_ids.filtered(lambda line: line.tax_line_id)
            )
        )
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")
        self.assertEqual(1, len(invoice.tbai_invoice_ids))
        (
            root,
            signature_value,
        ) = invoice.sudo().tbai_invoice_ids.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)

    def test_invoice_irpf_taxes(self):
        invoice = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_irpf15, self.partner.id
        )
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")
        self.assertEqual(1, len(invoice.tbai_invoice_ids))
        (
            root,
            signature_value,
        ) = invoice.sudo().tbai_invoice_ids.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)

    def test_invoice_equivalence_surcharge_taxes(self):
        invoice = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_surcharge, self.partner.id
        )
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")
        self.assertEqual(1, len(invoice.tbai_invoice_ids))
        (
            root,
            signature_value,
        ) = invoice.sudo().tbai_invoice_ids.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)

    def test_out_refund_refund(self):
        invoice = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_national, self.partner.id
        )
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")
        self.assertEqual(1, len(invoice.tbai_invoice_ids))
        (
            root,
            signature_value,
        ) = invoice.sudo().tbai_invoice_ids.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)
        # Create an invoice refund by differences
        account_move_reversal = (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=[invoice.id])
            .create(
                dict(
                    reason="Credit Note for Binovo",
                    date=date.today(),
                    refund_method="refund",
                )
            )
        )
        account_move_reversal.with_context(refund_method="refund").reverse_moves()
        self.assertEqual(1, len(invoice.reversal_move_id))
        refund = invoice.reversal_move_id
        self.assertEqual("I", refund.tbai_refund_type)
        self.assertEqual("R1", refund.tbai_refund_key)
        refund.action_post()
        self.assertEqual(refund.state, "posted")
        self.assertEqual(1, len(refund.tbai_invoice_ids))
        (
            r_root,
            r_signature_value,
        ) = refund.sudo().tbai_invoice_ids.get_tbai_xml_signed_and_signature_value()
        r_res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, r_root)
        self.assertTrue(r_res)

    def test_out_refund_refund_not_sent_invoice(self):
        self.main_company.tbai_enabled = False
        invoice = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_national, self.partner.id
        )
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")
        self.assertEqual(0, len(invoice.tbai_invoice_ids))
        self.main_company.tbai_enabled = True
        # Create an invoice refund by differences
        account_move_reversal = (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=[invoice.id])
            .create(
                dict(
                    reason="Credit Note for Binovo",
                    date=date.today(),
                    refund_method="refund",
                )
            )
        )
        account_move_reversal.with_context(refund_method="refund").reverse_moves()
        self.assertEqual(1, len(invoice.reversal_move_id))
        refund = invoice.reversal_move_id
        self.assertEqual("I", refund.tbai_refund_type)
        self.assertEqual("R1", refund.tbai_refund_key)
        refund.action_post()
        self.assertEqual(refund.state, "posted")
        self.assertEqual(0, len(refund.tbai_invoice_ids))

    def test_out_refund_modify(self):
        invoice = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_national, self.partner.id
        )
        invoice.invoice_origin = "TBAI-REFUND-MODIFY-TEST"
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")
        self.assertEqual(1, len(invoice.tbai_invoice_ids))
        (
            root,
            signature_value,
        ) = invoice.sudo().tbai_invoice_ids.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)
        # Create an invoice refund by substitution
        account_move_reversal = (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=[invoice.id])
            .create(
                dict(
                    reason="Credit Note for Binovo",
                    date=date.today(),
                    refund_method="modify",
                )
            )
        )
        account_move_reversal.with_context(refund_method="modify").reverse_moves()
        self.assertEqual(1, len(invoice.reversal_move_id))
        refund = invoice.reversal_move_id
        self.assertEqual(refund.payment_state, "paid")
        refund_invoice = invoice.reversal_move_id[0]
        self.assertEqual("I", refund_invoice.tbai_refund_type)
        self.assertEqual("R1", refund_invoice.tbai_refund_key)
        self.assertEqual(1, len(refund_invoice.tbai_invoice_ids))
        substitute_invoice = self.env["account.move"].search(
            [
                ("move_type", "=", "out_invoice"),
                ("id", "!=", invoice.id),
                ("invoice_origin", "=", invoice.invoice_origin),
            ]
        )
        self.assertEqual(1, len(substitute_invoice))
        substitute_invoice.action_post()
        self.assertEqual(substitute_invoice.state, "posted")
        self.assertEqual(1, len(substitute_invoice.tbai_invoice_ids))
        invs = substitute_invoice.sudo().tbai_invoice_ids
        r_root, r_signature_value = invs.get_tbai_xml_signed_and_signature_value()
        r_res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, r_root)
        self.assertTrue(r_res)

    def test_out_refund_cancel(self):
        invoice = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_national, self.partner.id
        )
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")
        self.assertEqual(1, len(invoice.tbai_invoice_ids))
        (
            root,
            signature_value,
        ) = invoice.sudo().tbai_invoice_ids.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)
        # Create an invoice refund by substitution
        account_move_reversal = (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=[invoice.id])
            .create(
                dict(
                    reason="Credit Note for Binovo",
                    date=date.today(),
                    refund_method="cancel",
                )
            )
        )
        account_move_reversal.with_context(refund_method="cancel").reverse_moves()
        self.assertEqual(1, len(invoice.reversal_move_id))
        refund = invoice.reversal_move_id
        self.assertEqual("I", refund.tbai_refund_type)
        self.assertEqual("R1", refund.tbai_refund_key)
        self.assertEqual(refund.payment_state, "paid")
        self.assertEqual(1, len(refund.tbai_invoice_ids))
        (
            r_root,
            r_signature_value,
        ) = refund.sudo().tbai_invoice_ids.get_tbai_xml_signed_and_signature_value()
        r_res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, r_root)
        self.assertTrue(r_res)
