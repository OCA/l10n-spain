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

    def test_resequence_customer(self):
        self.main_company.tbai_enabled = True
        invoice = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_national, self.partner.id
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

    def test_invoice_operation_desc(self):
        self.main_company.tbai_description_method = "manual"
        invoice = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_national, self.partner.id
        )
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        self.assertEqual(invoice.tbai_description_operation, "/")
        self.main_company.tbai_description_method = "fixed"
        description = "description test"
        self.main_company.tbai_description = description
        invoice._compute_tbai_description()
        self.assertEqual(invoice.tbai_description_operation, description)
        self.main_company.tbai_description_method = "auto"
        description = ""
        for line in invoice.invoice_line_ids:
            description += (line.name or line.ref) + " - "
        description = description[:-3]
        invoice._compute_tbai_description()
        self.assertEqual(invoice.tbai_description_operation, description)

    def test_invoice_foreign_currency(self):
        invoice = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_national, self.partner.id
        )
        usd_currency = self.env.ref("base.USD")
        if not usd_currency.active:
            usd_currency.active = True
        invoice.currency_id = usd_currency
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

    def test_invoice_non_tbai_journal(self):
        invoice = self.create_draft_invoice(
            self.account_billing.id,
            self.fiscal_position_national,
            self.partner.id,
            journal_id=self.non_tbai_journal,
        )
        # invoice.journal_id = self.non_tbai_journal
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")
        self.assertEqual(0, len(invoice.tbai_invoice_ids))

    def test_cancel_and_recreate(self):
        # Build three invoices and check the chaining.
        invoice = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_national, self.partner.id
        )
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")
        self.assertEqual(invoice.tbai_invoice_id.state, "pending")
        self.assertEqual(
            self.main_company.tbai_last_invoice_id, invoice.tbai_invoice_id
        )

        invoice2 = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_national, self.partner.id
        )
        invoice2.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice2.action_post()
        self.assertEqual(invoice2.state, "posted")
        self.assertEqual(invoice2.tbai_invoice_id.state, "pending")
        self.assertEqual(
            self.main_company.tbai_last_invoice_id, invoice2.tbai_invoice_id
        )

        invoice3 = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_national, self.partner.id
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
        tax = invoice.invoice_line_ids.filtered(
            lambda line: any([t.id == self.tax_iva0_sp_i.id for t in line.tax_ids])
        ).mapped("tax_ids")

        fp_tbai_tax = self.env["account.fp.tbai.tax"].search(
            [("tax_id", "=", tax.id), ("position_id", "=", self.fiscal_position_ic.id)],
            limit=1,
        )

        self.assertEqual(
            fp_tbai_tax.tbai_vat_exemption_key,
            self.vat_exemption_E5,
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
                    journal_id=self.tbai_journal.id,
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

    def test_out_refund_inconsistent_state_raises(self):
        invoice = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_national, self.partner.id
        )
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")
        self.assertEqual(1, len(invoice.tbai_invoice_ids))
        invoice.sudo().tbai_invoice_ids.state = "cancel"
        # Create an invoice refund by differences
        account_move_reversal = (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=[invoice.id])
            .create(
                dict(
                    reason="Credit Note for Binovo",
                    date=date.today(),
                    refund_method="refund",
                    journal_id=self.tbai_journal.id,
                )
            )
        )
        account_move_reversal.with_context(refund_method="refund").reverse_moves()
        refund = invoice.reversal_move_id
        with self.assertRaises(exceptions.ValidationError):
            refund.action_post()

    def test_out_refund_cancelled_raises(self):
        invoice = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_national, self.partner.id
        )
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")
        self.assertEqual(1, len(invoice.tbai_invoice_ids))
        invoice.tbai_cancellation_id = invoice.tbai_invoice_ids
        # Create an invoice refund by differences
        account_move_reversal = (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=[invoice.id])
            .create(
                dict(
                    reason="Credit Note for Binovo",
                    date=date.today(),
                    refund_method="refund",
                    journal_id=self.tbai_journal.id,
                )
            )
        )
        account_move_reversal.with_context(refund_method="refund").reverse_moves()
        refund = invoice.reversal_move_id
        with self.assertRaises(exceptions.ValidationError):
            refund.action_post()

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
                    journal_id=self.tbai_journal.id,
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
                    journal_id=self.tbai_journal.id,
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
                    journal_id=self.tbai_journal.id,
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

    def test_invoice_lines_protected_data(self):
        invoice = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_national, self.partner.id
        )
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        self.main_company.tbai_protected_data = True
        invoice.action_post()
        (
            root,
            signature_value,
        ) = invoice.sudo().tbai_invoice_ids.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)
        invoice_line_details = (
            root.findall("Factura")[0]
            .findall("DatosFactura")[0]
            .findall("DetallesFactura")[0]
            .findall("IDDetalleFactura")
        )
        for invoice_line_detail in invoice_line_details:
            invoice_line_description = invoice_line_detail.findall(
                "DescripcionDetalle"
            )[0]
            self.assertEqual(
                invoice_line_description.text, self.main_company.tbai_protected_data_txt
            )

    def test_invoice_line_iva_exento(self):
        invoice = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_national, self.partner.id
        )
        product_iva_exento = self.create_product(
            product_name="Servicio Exento",
            product_type="service",
            product_taxes=[self.tax_iva0_exento_sujeto.id],
        )
        invoice.write(
            {
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "move_id": invoice.id,
                            "product_id": product_iva_exento.id,
                            "quantity": 1,
                            "price_unit": 100.0,
                            "name": "TBAI Invoice Line Test - service IVA Exento",
                            "account_id": self.account_revenue.id,
                        },
                    )
                ]
            }
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

    def test_invoice_out_refund_from_origin(self):
        invoice = self.create_draft_invoice(
            self.account_billing.id,
            self.fiscal_position_national,
            self.partner.id,
            invoice_type="out_refund",
        )
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        self.assertEqual(invoice.move_type, "out_refund")
        invoice.sudo().tbai_refund_origin_ids = [
            (
                0,
                0,
                {
                    "number_prefix": "INV_XYZ/2021/",
                    "number": "001",
                    "expedition_date": "1901-01-01",
                },
            )
        ]
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")
        self.assertEqual(1, len(invoice.tbai_refund_origin_ids))
        self.assertEqual(1, len(invoice.tbai_invoice_ids))
        self.assertEqual(1, len(invoice.tbai_invoice_ids[0].tbai_invoice_refund_ids))
        self.assertEqual(
            "INV_XYZ/2021/",
            invoice.tbai_invoice_ids[0].tbai_invoice_refund_ids.number_prefix,
        )
        self.assertEqual(
            "001", invoice.tbai_invoice_ids[0].tbai_invoice_refund_ids.number
        )
        self.assertEqual(
            "01-01-1901",
            invoice.tbai_invoice_ids[0].tbai_invoice_refund_ids.expedition_date,
        )

    def test_invoice_out_refund_from_origin_error_path_origin_missing(self):
        invoice = self.create_draft_invoice(
            self.account_billing.id,
            self.fiscal_position_national,
            self.partner.id,
            invoice_type="out_refund",
        )
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        self.assertEqual(invoice.move_type, "out_refund")
        invoice.sudo().tbai_refund_origin_ids = False
        with self.assertRaises(exceptions.ValidationError):
            invoice.action_post()

    def test_invoice_out_refund_from_origin_number_too_long(self):
        invoice = self.create_draft_invoice(
            self.account_billing.id,
            self.fiscal_position_national,
            self.partner.id,
            invoice_type="out_refund",
        )
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        with self.assertRaises(exceptions.ValidationError):
            invoice.sudo().tbai_refund_origin_ids = [
                (
                    0,
                    0,
                    {
                        "number_prefix": "INV_XYZ/2021/",
                        "number": "000000000000000000001",
                        "expedition_date": "1901-01-01",
                    },
                )
            ]

    def test_invoice_out_refund_from_origin_prefix_too_long(self):
        invoice = self.create_draft_invoice(
            self.account_billing.id,
            self.fiscal_position_national,
            self.partner.id,
            invoice_type="out_refund",
        )
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        with self.assertRaises(exceptions.ValidationError):
            invoice.sudo().tbai_refund_origin_ids = [
                (
                    0,
                    0,
                    {
                        "number_prefix": "S00000000000000000000",
                        "number": "01",
                        "expedition_date": "1901-01-01",
                    },
                )
            ]
