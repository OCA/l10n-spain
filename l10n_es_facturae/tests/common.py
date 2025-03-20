# Copyright 2016 Serv. Tecnol. Avanzados - Pedro M. Baeza
# Copyright 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64
from datetime import timedelta
from unittest import mock

import xmlsig
from lxml import etree

from odoo import exceptions, fields
from odoo.tests import tagged
from odoo.tools.misc import mute_logger

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_certificate import (
    TestL10nEsAeatCertificateBase,
)


@tagged("post_install", "-at_install")
class CommonTestBase(TestL10nEsAeatCertificateBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        self = cls
        self.tax = self.env["account.tax"].create(
            {
                "name": "Test tax",
                "amount_type": "percent",
                "amount": 21,
                "type_tax_use": "sale",
                "facturae_code": "01",
                "country_id": cls.env.ref("base.es").id,
            }
        )

        self.state = self.env["res.country.state"].create(
            {
                "name": "Ciudad Real",
                "code": "13",
                "country_id": self.env.ref("base.es").id,
            }
        )
        self.partner = self.env["res.partner"].create(
            {
                "name": "Cliente de prueba",
                "street": "C/ Ejemplo, 13",
                "zip": "13700",
                "city": "Tomelloso",
                "state_id": self.state.id,
                "country_id": self.env.ref("base.es").id,
                "vat": "ES05680675C",
                "facturae": True,
                "attach_invoice_as_annex": False,
                "organo_gestor": "U00000038",
                "unidad_tramitadora": "U00000038",
                "oficina_contable": "U00000038",
            }
        )
        main_company = self.env.ref("base.main_company")
        main_company.vat = "ESA12345674"
        main_company.partner_id.country_id = self.env.ref("base.es")
        if not main_company.chart_template_id:
            # Load a CoA if there's none in the company
            coa = cls.env.ref("l10n_generic_coa.configurable_chart_template", False)
            if not coa:
                # Load the first available CoA
                coa = cls.env["account.chart.template"].search(
                    [("visible", "=", True)], limit=1
                )
            coa.try_loading(company=main_company, install_demo=False)
        self.env["res.currency.rate"].search(
            [("currency_id", "=", main_company.currency_id.id)]
        ).write({"company_id": False})
        bank_obj = self.env["res.partner.bank"]
        self.bank = bank_obj.search(
            [("acc_number", "=", "FR20 1242 1242 1242 1242 1242 124")], limit=1
        )
        if not self.bank:
            self.bank = bank_obj.create(
                {
                    "acc_number": "FR20 1242 1242 1242 1242 1242 124",
                    "partner_id": main_company.partner.id,
                    "bank_id": self.env["res.bank"]
                    .search([("bic", "=", "PSSTFRPPXXX")], limit=1)
                    .id,
                }
            )
        self.payment_method = self.env.ref("account.account_payment_method_manual_in")
        payment_methods = self.env["account.payment.method"].search(
            [("payment_type", "=", "inbound")]
        )
        self.journal = self.env["account.journal"].create(
            {
                "name": "Test journal",
                "code": "TEST",
                "type": "bank",
                "company_id": main_company.id,
                "bank_account_id": self.bank.id,
                "inbound_payment_method_line_ids": [
                    (0, 0, {"payment_method_id": x.id}) for x in payment_methods
                ],
            }
        )

        self.sale_journal = self.env["account.journal"].create(
            {
                "name": "Sale journal",
                "code": "SALE_TEST",
                "type": "sale",
                "company_id": main_company.id,
            }
        )
        self.refund_payment_mode = self.env["account.payment.mode"].create(
            {
                "name": "Test payment mode Refund",
                "bank_account_link": "fixed",
                "fixed_journal_id": self.journal.id,
                "payment_method_id": self.env.ref(
                    "account.account_payment_method_manual_out"
                ).id,
                "show_bank_account_from_journal": True,
                "facturae_code": "01",
            }
        )
        self.payment_mode = self.env["account.payment.mode"].create(
            {
                "name": "Test payment mode",
                "bank_account_link": "fixed",
                "fixed_journal_id": self.journal.id,
                "payment_method_id": self.payment_method.id,
                "show_bank_account_from_journal": True,
                "facturae_code": "01",
                "refund_payment_mode_id": self.refund_payment_mode.id,
            }
        )

        self.payment_mode_02 = self.env["account.payment.mode"].create(
            {
                "name": "Test payment mode 02",
                "bank_account_link": "fixed",
                "fixed_journal_id": self.journal.id,
                "payment_method_id": self.payment_method.id,
                "show_bank_account_from_journal": True,
                "facturae_code": "02",
                "refund_payment_mode_id": self.refund_payment_mode.id,
            }
        )

        self.account = self.env["account.account"].create(
            {
                "company_id": main_company.id,
                "name": "Facturae Product account",
                "code": "facturae.product",
                "account_type": "income_other",
            }
        )
        self.move = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "journal_id": self.sale_journal.id,
                "invoice_date": "2016-03-12",
                "payment_mode_id": self.payment_mode.id,
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.env.ref(
                                "product.product_delivery_02"
                            ).id,
                            "account_id": self.account.id,
                            "name": "Producto de prueba",
                            "quantity": 1.0,
                            "price_unit": 100.0,
                            "tax_ids": [(6, 0, self.tax.ids)],
                        },
                    )
                ],
            }
        )
        self.move_line = self.move.invoice_line_ids

        self.move_02 = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "journal_id": self.sale_journal.id,
                "invoice_date": "2016-03-12",
                "payment_mode_id": self.payment_mode_02.id,
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.env.ref(
                                "product.product_delivery_02"
                            ).id,
                            "account_id": self.account.id,
                            "name": "Producto de prueba",
                            "quantity": 1.0,
                            "price_unit": 100.0,
                            "tax_ids": [(6, 0, self.tax.ids)],
                        },
                    )
                ],
            }
        )
        self.move_line_02 = self.move_02.invoice_line_ids
        self.partner.vat = "ES05680675C"
        self.partner.is_company = False
        self.partner.name = "Cliente de Prueba"
        self.partner.country_id = self.env.ref("base.us")
        self.partner.state_id = self.env.ref("base.state_us_2")
        self.main_company = self.env.ref("base.main_company")
        self.wizard = self.env["create.facturae"].create({})
        self.fe = "http://www.facturae.es/Facturae/2009/v3.2/Facturae"
        self.first_check_amount = ["190.310000", "190.310000", "190.31", "39.97"]
        self.second_check_amount = [
            "190.310000",
            "133.220000",
            "133.22",
            "27.98",
            "57.090000",
        ]
        self.refund_move = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "journal_id": self.sale_journal.id,
                "invoice_date": "2016-03-12",
                "payment_mode_id": self.payment_mode_02.id,
                "move_type": "out_refund",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.env.ref(
                                "product.product_delivery_02"
                            ).id,
                            "account_id": self.account.id,
                            "name": "Producto de prueba",
                            "quantity": 1.0,
                            "price_unit": 100.0,
                            "tax_ids": [(6, 0, self.tax.ids)],
                        },
                    )
                ],
            }
        )
        self.refund_check_amount = ["-100.000000", "-100.000000", "-100.00", "-21.00"]
        self.refund_check_totals = ["-100.00", "-100.00", "-21.00", "-121.00"]
        self.hided_discount_check_amount = [
            "133.217000",
            "133.220000",
            "133.22",
            "27.98",
        ]


class CommonTest(CommonTestBase):
    def _create_facturae_file(self, move_id, force=False):
        wizard = (
            self.env["create.facturae"]
            .with_context(
                force_report_rendering=force,
                active_ids=move_id.ids,
                active_model="account.move",
            )
            .create({})
        )
        wizard.create_facturae_file()
        return etree.fromstring(base64.b64decode(wizard.facturae))

    def test_facturae_generation(self):
        self.move.action_post()
        self._activate_certificate(self.certificate_password)
        self.move.name = "2999/99999"
        generated_facturae = self._create_facturae_file(self.move)
        self.assertEqual(
            generated_facturae.xpath(
                "/fe:Facturae/Parties/SellerParty/TaxIdentification/"
                "TaxIdentificationNumber",
                namespaces={"fe": self.fe},
            )[0].text,
            self.env.ref("base.main_company").vat,
        )
        self.assertEqual(
            generated_facturae.xpath(
                "/fe:Facturae/Invoices/Invoice/InvoiceHeader/InvoiceNumber",
                namespaces={"fe": self.fe},
            )[0].text,
            self.move.name,
        )
        self.assertFalse(
            generated_facturae.xpath(
                "/fe:Facturae/Invoices/Invoice/AdditionalData/"
                "RelatedDocuments/Attachments",
                namespaces={"fe": self.fe},
            ),
        )

    def test_facturae_with_attachments(self):
        self._activate_certificate(self.certificate_password)
        self.move.action_post()
        self.move.name = "2999/99999"
        self.partner.attach_invoice_as_annex = True
        with mock.patch(
            "odoo.addons.base.models.ir_actions_report.IrActionsReport._render_qweb_pdf"
        ) as ptch:
            ptch.return_value = (b"1234", "pdf")
            generated_facturae = self._create_facturae_file(self.move, force=True)
        self.assertTrue(
            generated_facturae.xpath(
                "/fe:Facturae/Invoices/Invoice/AdditionalData/RelatedDocuments",
                namespaces={"fe": self.fe},
            ),
        )
        self.assertTrue(
            generated_facturae.xpath(
                "/fe:Facturae/Invoices/Invoice/AdditionalData/"
                "RelatedDocuments/Attachment",
                namespaces={"fe": self.fe},
            ),
        )

    def test_facturae_with_extra_attachments(self):
        self._activate_certificate(self.certificate_password)
        self.move.action_post()
        self.move.name = "2999/99999"
        self.partner.attach_invoice_as_annex = False
        self.move.write(
            {
                "l10n_es_facturae_attachment_ids": [
                    (
                        0,
                        0,
                        {
                            "filename": "new_file.pdf",
                            "file": base64.b64encode(b"DEMO FILE"),
                        },
                    )
                ]
            }
        )
        generated_facturae = self._create_facturae_file(self.move, force=True)
        self.assertTrue(
            generated_facturae.xpath(
                "/fe:Facturae/Invoices/Invoice/AdditionalData/" "RelatedDocuments",
                namespaces={"fe": self.fe},
            ),
        )
        self.assertTrue(
            generated_facturae.xpath(
                "/fe:Facturae/Invoices/Invoice/AdditionalData/"
                "RelatedDocuments/Attachment",
                namespaces={"fe": self.fe},
            ),
        )

    def test_bank(self):
        self.bank.bank_id.bic = "CAIXESBB"
        with self.assertRaises(exceptions.ValidationError):
            self.move.validate_facturae_fields()
        with self.assertRaises(exceptions.ValidationError):
            self.move_02.validate_facturae_fields()
        self.bank.bank_id.bic = "CAIXESBBXXX"
        self.bank.acc_number = "1111"
        with self.assertRaises(exceptions.ValidationError):
            self.move.validate_facturae_fields()
        with self.assertRaises(exceptions.ValidationError):
            self.move_02.validate_facturae_fields()
        self.bank.acc_number = "BE96 9988 7766 5544"

    def test_validation_error(self):
        self._activate_certificate(self.certificate_password)
        self.main_company.partner_id.country_id = False
        self.move.action_post()
        self.move.name = "2999/99999"
        with self.assertRaises(exceptions.UserError), mute_logger(
            "odoo.addons.l10n_es_facturae.reports.report_facturae"
        ):
            self._create_facturae_file(self.move)

    def test_signature(self):
        self._activate_certificate(self.certificate_password)
        self.move.action_post()
        self.move.name = "2999/99999"
        self.main_company.partner_id.country_id = self.env.ref("base.es")
        generated_facturae = self._create_facturae_file(self.move)
        ns = "http://www.w3.org/2000/09/xmldsig#"
        self.assertEqual(
            len(generated_facturae.xpath("//ds:Signature", namespaces={"ds": ns})), 1
        )

        node = generated_facturae.find(".//ds:Signature", {"ds": ns})
        ctx = xmlsig.SignatureContext()
        verification_error = False
        error_message = ""
        try:
            ctx.verify(node)
        except Exception as e:
            verification_error = True
            error_message = str(e)
        self.assertEqual(
            verification_error,
            False,
            "Error found during verification of the signature of "
            + "the move: %s" % error_message,
        )

    def test_refund(self):
        self._activate_certificate(self.certificate_password)
        self.move.action_post()
        self.move.name = "2999/99999"
        motive = "Description motive"
        refund = (
            self.env["account.move.reversal"]
            .with_context(active_ids=self.move.ids, active_model=self.move._name)
            .create(
                {
                    "refund_reason": "01",
                    "reason": motive,
                    "journal_id": self.move.journal_id.id,
                }
            )
        )
        refund_result = refund.reverse_moves()
        domain = refund_result.get("domain", False)
        if not domain:
            domain = [("id", "=", refund_result["res_id"])]
        refund_inv = self.env["account.move"].search(domain)
        self.assertTrue(refund_inv)
        self.assertIn(motive, refund_inv.ref)
        self.assertEqual(refund_inv.facturae_refund_reason, "01")
        refund_inv.action_post()
        refund_inv.name = "2998/99999"
        self.wizard.with_context(
            active_ids=refund_inv.ids, active_model="account.move"
        ).create_facturae_file()
        with self.assertRaises(exceptions.UserError):
            self.wizard.with_context(
                active_ids=[self.move_02.id, self.move.id],
                active_model="account.move",
            ).create_facturae_file()

    def test_refund_amounts_file_generation(self):
        self._activate_certificate(self.certificate_password)
        self._check_amounts(self.refund_move, *self.refund_check_amount)

    def test_refund_totals_file_generation(self):
        self._activate_certificate(self.certificate_password)
        self._check_totals(self.refund_move, *self.refund_check_totals)

    def test_constrains_01(self):
        move = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "journal_id": self.journal.id,
                "invoice_date": "2016-03-12",
                "payment_mode_id": self.payment_mode.id,
            }
        )
        line = self.env["account.move.line"].create(
            {
                "product_id": self.env.ref("product.product_delivery_02").id,
                "account_id": self.account.id,
                "move_id": move.id,
                "name": "Producto de prueba",
                "quantity": 1.0,
                "price_unit": 100.0,
                "tax_ids": [(6, 0, self.tax.ids)],
            }
        )
        with self.assertRaises(exceptions.ValidationError):
            line.facturae_start_date = fields.Date.today()

    def test_constrains_02(self):
        move = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "journal_id": self.journal.id,
                "invoice_date": "2016-03-12",
                "payment_mode_id": self.payment_mode.id,
            }
        )
        line = self.env["account.move.line"].create(
            {
                "product_id": self.env.ref("product.product_delivery_02").id,
                "account_id": self.account.id,
                "move_id": move.id,
                "name": "Producto de prueba",
                "quantity": 1.0,
                "price_unit": 100.0,
                "tax_ids": [(6, 0, self.tax.ids)],
            }
        )
        with self.assertRaises(exceptions.ValidationError):
            line.facturae_end_date = fields.Date.today()

    def test_constrains_03(self):
        move = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "journal_id": self.journal.id,
                "invoice_date": "2016-03-12",
                "payment_mode_id": self.payment_mode.id,
            }
        )
        line = self.env["account.move.line"].create(
            {
                "product_id": self.env.ref("product.product_delivery_02").id,
                "account_id": self.account.id,
                "move_id": move.id,
                "name": "Producto de prueba",
                "quantity": 1.0,
                "price_unit": 100.0,
                "tax_ids": [(6, 0, self.tax.ids)],
            }
        )
        with self.assertRaises(exceptions.ValidationError):
            line.write(
                {
                    "facturae_end_date": fields.Date.today(),
                    "facturae_start_date": fields.Date.to_string(
                        fields.Date.to_date(fields.Date.today()) + timedelta(days=1)
                    ),
                }
            )

    def test_constrains_04(self):
        move = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "journal_id": self.journal.id,
                "invoice_date": "2016-03-12",
                "payment_mode_id": self.payment_mode.id,
            }
        )
        with self.assertRaises(exceptions.ValidationError):
            move.facturae_start_date = fields.Date.today()

    def test_constrains_05(self):
        move = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "journal_id": self.journal.id,
                "invoice_date": "2016-03-12",
                "payment_mode_id": self.payment_mode.id,
            }
        )
        with self.assertRaises(exceptions.ValidationError):
            move.facturae_end_date = fields.Date.today()

    def test_constrains_06(self):
        move = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "journal_id": self.journal.id,
                "invoice_date": "2016-03-12",
                "payment_mode_id": self.payment_mode.id,
            }
        )
        with self.assertRaises(exceptions.ValidationError):
            move.write(
                {
                    "facturae_end_date": fields.Date.today(),
                    "facturae_start_date": fields.Date.to_string(
                        fields.Date.to_date(fields.Date.today()) + timedelta(days=1)
                    ),
                }
            )

    def test_views(self):
        action = self.move_line.button_edit_facturae_fields()
        item = self.env[action["res_model"]].browse(action["res_id"])
        self.assertEqual(item, self.move_line)

    def _check_amounts(self, move, wo_discount, subtotal, base, tax, discount=0):
        if move.state != "posted":
            move.action_post()
            move.name = "2999/99999"
        facturae_xml = self._create_facturae_file(move)
        self.assertEqual(
            facturae_xml.xpath("//InvoiceLine/TotalCost")[0].text,
            wo_discount,
        )
        self.assertEqual(
            facturae_xml.xpath("//InvoiceLine/GrossAmount")[0].text,
            subtotal,
        )
        self.assertEqual(
            facturae_xml.xpath("//TaxesOutputs//TaxableBase/TotalAmount")[0].text,
            base,
        )
        self.assertEqual(
            facturae_xml.xpath("//TaxesOutputs//TaxAmount/TotalAmount")[0].text,
            tax,
        )
        if discount:
            self.assertEqual(
                facturae_xml.xpath("//InvoiceLine//DiscountAmount")[0].text,
                discount,
            )

    def _check_totals(self, move, subtotal, base, tax, total):
        move.action_post()
        move.name = "2999/99999"
        move.facturae_withheld_reason = "WithholdingReason"
        move.facturae_withheld_percent = 0.05
        generated_facturae = self._create_facturae_file(move)
        self.assertEqual(
            generated_facturae.xpath("//InvoiceTotals/TotalGrossAmount")[0].text,
            subtotal,
        )
        self.assertEqual(
            generated_facturae.xpath("//InvoiceTotals/TotalGrossAmountBeforeTaxes")[
                0
            ].text,
            base,
        )
        self.assertEqual(
            generated_facturae.xpath("//InvoiceTotals/TotalTaxOutputs")[0].text,
            tax,
        )
        self.assertEqual(
            generated_facturae.xpath("//InvoiceTotals//InvoiceTotal")[0].text,
            total,
        )
        self.assertEqual(
            generated_facturae.xpath(
                "//InvoiceTotals//AmountsWithheld//WithholdingReason"
            )[0].text,
            "WithholdingReason",
        )
        version = move.get_facturae_version()
        self.assertEqual(
            generated_facturae.xpath(
                "//InvoiceTotals//AmountsWithheld//WithholdingRate"
            )[0].text,
            ("%.4f" if version == "3_2" else "%.8f") % 5,
        )
        self.assertEqual(
            generated_facturae.xpath(
                "//InvoiceTotals//AmountsWithheld//WithholdingAmount"
            )[0].text,
            ("%.2f" if version == "3_2" else "%.8f") % 5,
        )
        sign = -1 if move.move_type == "out_refund" else 1
        self.assertEqual(
            generated_facturae.xpath("//InvoiceTotals//TotalExecutableAmount")[0].text,
            ("%.2f" if version == "3_2" else "%.8f") % (float(total) - (sign * 5)),
        )

    def test_move_rounding(self):
        self._activate_certificate(self.certificate_password)
        self.main_company.tax_calculation_rounding_method = "round_globally"
        dp = self.env.ref("product.decimal_price")
        dp.digits = 4
        # We do this for refreshing the cached value in this env
        self.assertEqual(dp.precision_get(dp.name), 4)
        move = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "journal_id": self.sale_journal.id,
                "invoice_date": "2016-03-12",
                "payment_mode_id": self.payment_mode.id,
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.env.ref(
                                "product.product_delivery_02"
                            ).id,
                            "account_id": self.account.id,
                            "name": "Producto de prueba",
                            "quantity": 1.0,
                            "price_unit": 190.314,
                            "tax_ids": [(6, 0, self.tax.ids)],
                        },
                    )
                ],
            }
        )
        self.assertAlmostEqual(move.invoice_line_ids.price_unit, 190.314, 4)
        self._check_amounts(move, *self.first_check_amount)

    def test_move_rounding_with_discount(self):
        self._activate_certificate(self.certificate_password)
        self.main_company.tax_calculation_rounding_method = "round_globally"
        dp = self.env.ref("product.decimal_price")
        dp.digits = 4
        # We do this for refreshing the cached value in this env
        self.assertEqual(dp.precision_get(dp.name), 4)
        move = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "journal_id": self.sale_journal.id,
                "invoice_date": "2016-03-12",
                "payment_mode_id": self.payment_mode.id,
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.env.ref(
                                "product.product_delivery_02"
                            ).id,
                            "account_id": self.account.id,
                            "name": "Producto de prueba",
                            "quantity": 1.0,
                            "price_unit": 190.314,
                            "discount": 30,
                            "tax_ids": [(6, 0, self.tax.ids)],
                        },
                    )
                ],
            }
        )
        self._check_amounts(move, *self.second_check_amount)

    def test_hide_discount(self):
        self._activate_certificate(self.certificate_password)
        self.main_company.tax_calculation_rounding_method = "round_globally"
        dp = self.env.ref("product.decimal_price")
        dp.digits = 4
        # We do this for refreshing the cached value in this env
        self.assertEqual(dp.precision_get(dp.name), 4)
        move = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "journal_id": self.sale_journal.id,
                "invoice_date": "2016-03-12",
                "payment_mode_id": self.payment_mode.id,
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.env.ref(
                                "product.product_delivery_02"
                            ).id,
                            "account_id": self.account.id,
                            "name": "Producto de prueba",
                            "quantity": 1.0,
                            "price_unit": 190.314,
                            "discount": 30,
                            "tax_ids": [(6, 0, self.tax.ids)],
                        },
                    )
                ],
            }
        )
        # Check amouns and discount with facturae_hide_discount in company
        self.main_company.facturae_hide_discount = True
        self._check_amounts(move, *self.hided_discount_check_amount)
        facturae_xml = self._create_facturae_file(move)
        self.assertFalse(
            facturae_xml.xpath("//InvoiceLine//DiscountAmount"),
        )
        # Check amouns and discount with facturae_hide_discount in partner_id
        self.main_company.facturae_hide_discount = False
        self.partner.facturae_hide_discount = True
        self._check_amounts(move, *self.hided_discount_check_amount)
        facturae_xml = self._create_facturae_file(move)
        self.assertFalse(
            facturae_xml.xpath("//InvoiceLine//DiscountAmount"),
        )

    def test_facturae_commercial_field(self):
        child_partner = self.partner.copy()
        child_partner.name = "Child partner"
        child_partner.parent_id = self.partner.id
        self.assertEqual(child_partner.facturae, self.partner.facturae)
        self.partner.facturae = False
        self.assertEqual(child_partner.facturae, self.partner.facturae)

    def _create_wizard_facturae_file(self):
        self.move.action_post()
        self._activate_certificate(self.certificate_password)
        self.move.name = "2999/99999"
        wizard = (
            self.env["create.facturae"]
            .with_context(active_ids=self.move.ids, active_model="account.move")
            .create({})
        )
        return wizard

    def test_facturae_contact_creation_directly(self):
        """Create new child partner directly instead of parent form view"""
        new_partner = self.env["res.partner"].create(
            {
                "name": "test contact child",
                "type": "contact",
                "parent_id": self.partner.id,
            }
        )
        self.assertTrue(new_partner)
