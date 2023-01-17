# Copyright 2016 Serv. Tecnol. Avanzados - Pedro M. Baeza
# Copyright 2017 Creu Blanca
# Copyright 2023 QubiQ - Jan Tugores (jan.tugores@qubiq.es)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64
from datetime import timedelta

from lxml import etree
from mock import patch

from odoo import exceptions, fields
from odoo.tools.misc import mute_logger

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_certificate import (
    TestL10nEsAeatCertificateBase,
)


class CommonTest(TestL10nEsAeatCertificateBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # We want to avoid testing on the CommonTest class
        if (
            self.test_class == "CommonTest"
            and self.__module__ == "odoo.addons.l10n_es_facturae.tests.common"
        ):
            self.test_tags -= {"at_install"}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        self = cls
        main_company = self.env.ref("base.main_company")
        main_company.vat = "ESA12345674"
        main_company.partner_id.country_id = self.env.ref("base.uk")
        main_company.partner_id.street = "Street"
        main_company.partner_id.city = "City"
        main_company.partner_id.zip = "00001"
        self.tax = self.env["account.tax"].create(
            {
                "name": "Test tax",
                "amount_type": "percent",
                "amount": 21,
                "type_tax_use": "sale",
                "facturae_code": "01",
                "company_id": main_company.id,
            }
        )

        self.state = self.env["res.country.state"].create(
            {
                "name": "Ciudad Real",
                "code": "13",
                "country_id": self.env.ref("base.es").id,
            }
        )
        main_company.partner_id.state_id = self.state.id
        self.partner = self.env["res.partner"].create(
            {
                "name": "Cliente de prueba",
                "company_id": main_company.id,
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
        self.product = self.env["product.product"].create(
            {"name": "Product 1", "company_id": main_company.id}
        )
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
                    "partner_id": main_company.partner_id.id,
                    "bank_id": self.env["res.bank"]
                    .search([("bic", "=", "PSSTFRPPXXX")], limit=1)
                    .id,
                    "company_id": main_company.id,
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
                "company_id": main_company.id,
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
                "company_id": main_company.id,
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
                "company_id": main_company.id,
            }
        )

        self.account = self.env["account.account"].create(
            {
                "company_id": main_company.id,
                "name": "Facturae Product account",
                "code": "facturae_product",
                "user_type_id": self.env.ref("account.data_account_type_revenue").id,
            }
        )
        self.move = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "company_id": main_company.id,
                "journal_id": self.sale_journal.id,
                "invoice_date": "2016-03-12",
                "payment_mode_id": self.payment_mode.id,
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
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
        self.move.refresh()
        self.move_line = self.move.invoice_line_ids

        self.move_02 = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "company_id": main_company.id,
                "journal_id": self.sale_journal.id,
                "invoice_date": "2016-03-12",
                "payment_mode_id": self.payment_mode_02.id,
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
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
        self.move_02.refresh()

        self.move_line_02 = self.move_02.invoice_line_ids
        self.partner.vat = "ES05680675C"
        self.partner.is_company = False
        self.partner.name = "Cliente de Prueba"
        self.partner.country_id = self.env.ref("base.us")
        self.partner.state_id = self.env.ref("base.state_us_2")
        self.main_company = self.env.ref("base.main_company")
        self.wizard = (
            self.env["create.facturae"]
            .with_context(
                active_ids=self.move.ids,
                active_model="account.move",
            )
            .create({})
        )
        self.fe = "http://www.facturae.es/Facturae/2009/v3.2/Facturae"
        self.first_check_amount = ["190.310000", "190.310000", "190.31", "39.97"]
        self.second_check_amount = [
            "190.310000",
            "133.220000",
            "133.22",
            "27.98",
            "57.090000",
        ]

    def test_facturae_generation(self):
        self.move.action_post()
        self._activate_certificate(self.certificate_password)
        self.move.name = "2999/99999"
        self.wizard.with_context(
            active_ids=self.move.ids,
            active_model="account.move",
            skip_signature=True,
        ).create_facturae_file()
        generated_facturae = etree.fromstring(base64.b64decode(self.wizard.facturae))
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
        with patch(
            "odoo.addons.base.models.ir_actions_report.IrActionsReport._render_qweb_pdf"
        ) as ptch:
            ptch.return_value = (b"1234", "pdf")
            self.wizard.with_context(
                force_report_rendering=True,
                active_ids=self.move.ids,
                active_model="account.move",
                skip_signature=True,
            ).create_facturae_file()
        generated_facturae = etree.fromstring(base64.b64decode(self.wizard.facturae))
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
        self.wizard.with_context(
            force_report_rendering=True,
            active_ids=self.move.ids,
            active_model="account.move",
            skip_signature=True,
        ).create_facturae_file()
        generated_facturae = etree.fromstring(base64.b64decode(self.wizard.facturae))
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
            self.wizard.with_context(
                active_ids=self.move.ids,
                active_model="account.move",
                skip_signature=True,
            ).create_facturae_file()

    def test_signature(self):
        self._activate_certificate(self.certificate_password)
        self.move.action_post()
        self.move.name = "2999/99999"
        self.main_company.partner_id.country_id = self.env.ref("base.es")
        with self.assertRaises(exceptions.ValidationError):
            self.wizard.with_context(
                active_ids=self.move.ids,
                active_model="account.move",
            ).create_facturae_file()

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
                    "company_id": self.env.ref("base.main_company").id,
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
            active_ids=refund_inv.ids,
            active_model="account.move",
            skip_signature=True,
        ).create_facturae_file()
        with self.assertRaises(exceptions.UserError):
            self.wizard.with_context(
                active_ids=[self.move_02.id, self.move.id],
                active_model="account.move",
            ).create({})

    def test_constrains_01(self):
        move = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "company_id": self.env.ref("base.main_company").id,
                "journal_id": self.journal.id,
                "invoice_date": "2016-03-12",
                "payment_mode_id": self.payment_mode.id,
            }
        )
        line = self.env["account.move.line"].create(
            {
                "product_id": self.product.id,
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
                "company_id": self.env.ref("base.main_company").id,
                "journal_id": self.journal.id,
                "invoice_date": "2016-03-12",
                "payment_mode_id": self.payment_mode.id,
            }
        )
        line = self.env["account.move.line"].create(
            {
                "product_id": self.product.id,
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
                "company_id": self.env.ref("base.main_company").id,
                "journal_id": self.journal.id,
                "invoice_date": "2016-03-12",
                "payment_mode_id": self.payment_mode.id,
            }
        )
        line = self.env["account.move.line"].create(
            {
                "product_id": self.product.id,
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
                "company_id": self.env.ref("base.main_company").id,
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
                "company_id": self.env.ref("base.main_company").id,
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
                "company_id": self.env.ref("base.main_company").id,
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

    def test_validation_error_01(self):
        with self.assertRaises(exceptions.ValidationError):
            self.env["res.partner"].create(
                {
                    "name": "Cliente de prueba",
                    "company_id": self.env.ref("base.main_company").id,
                    "street": False,
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

    def test_validation_error_02(self):
        main_company = self.env.ref("base.main_company")
        main_company.partner_id.write(
            {
                "vat": False,
                "street": "Street",
                "city": "City",
                "state_id": self.state.id,
                "zip": "00001",
            }
        )
        move = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "company_id": self.env.ref("base.main_company").id,
                "journal_id": self.sale_journal.id,
                "invoice_date": "2016-03-12",
                "payment_mode_id": self.payment_mode.id,
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
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
        move.action_post()
        with self.assertRaises(exceptions.ValidationError):
            self.wizard.with_context(
                active_ids=move.ids,
                active_model="account.move",
                skip_signature=True,
            ).create_facturae_file()

    def test_validation_error_03(self):
        main_company = self.env.ref("base.main_company")
        main_company.partner_id.write(
            {
                "vat": "ESA12345674",
                "street": False,
                "city": "City",
                "state_id": self.state.id,
                "zip": "00001",
            }
        )
        move = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "company_id": self.env.ref("base.main_company").id,
                "journal_id": self.sale_journal.id,
                "invoice_date": "2016-03-12",
                "payment_mode_id": self.payment_mode.id,
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
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
        move.action_post()
        with self.assertRaises(exceptions.ValidationError):
            self.wizard.with_context(
                active_ids=move.ids,
                active_model="account.move",
                skip_signature=True,
            ).create_facturae_file()

    def test_validation_error_04(self):
        main_company = self.env.ref("base.main_company")
        main_company.partner_id.write(
            {
                "vat": "ESA12345674",
                "street": "Street",
                "city": False,
                "state_id": self.state.id,
                "zip": "00001",
            }
        )
        move = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "company_id": self.env.ref("base.main_company").id,
                "journal_id": self.sale_journal.id,
                "invoice_date": "2016-03-12",
                "payment_mode_id": self.payment_mode.id,
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
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
        move.action_post()
        with self.assertRaises(exceptions.ValidationError):
            self.wizard.with_context(
                active_ids=move.ids,
                active_model="account.move",
                skip_signature=True,
            ).create_facturae_file()

    def test_validation_error_05(self):
        main_company = self.env.ref("base.main_company")
        main_company.partner_id.write(
            {
                "vat": "ESA12345674",
                "street": "Street",
                "city": "City",
                "state_id": False,
                "zip": "00001",
            }
        )
        move = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "company_id": self.env.ref("base.main_company").id,
                "journal_id": self.sale_journal.id,
                "invoice_date": "2016-03-12",
                "payment_mode_id": self.payment_mode.id,
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
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
        move.action_post()
        with self.assertRaises(exceptions.ValidationError):
            self.wizard.with_context(
                active_ids=move.ids,
                active_model="account.move",
                skip_signature=True,
            ).create_facturae_file()

    def test_validation_error_06(self):
        main_company = self.env.ref("base.main_company")
        main_company.partner_id.write(
            {
                "vat": "ESA12345674",
                "street": "Street",
                "city": "City",
                "state_id": self.state.id,
                "zip": False,
            }
        )
        move = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "company_id": self.env.ref("base.main_company").id,
                "journal_id": self.sale_journal.id,
                "invoice_date": "2016-03-12",
                "payment_mode_id": self.payment_mode.id,
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
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
        move.action_post()
        with self.assertRaises(exceptions.ValidationError):
            self.wizard.with_context(
                active_ids=move.ids,
                active_model="account.move",
                skip_signature=True,
            ).create_facturae_file()

    def test_views(self):
        action = self.move_line.button_edit_facturae_fields()
        item = self.env[action["res_model"]].browse(action["res_id"])
        self.assertEqual(item, self.move_line)

    def _check_amounts(self, move, wo_discount, subtotal, base, tax, discount=0):
        move.action_post()
        move.name = "2999/99999"
        self.wizard.write({"move_id": move.id})
        self.wizard.with_context(skip_signature=True).create_facturae_file()
        facturae_xml = etree.fromstring(base64.b64decode(self.wizard.facturae))
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
                "company_id": self.env.ref("base.main_company").id,
                "journal_id": self.sale_journal.id,
                "invoice_date": "2016-03-12",
                "payment_mode_id": self.payment_mode.id,
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
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

    def test_facturae_not_enabled(self):
        partner_no_facturae = self.env["res.partner"].create(
            {
                "name": "Cliente de prueba",
                "company_id": self.env.ref("base.main_company").id,
                "street": "C/ Ejemplo, 13",
                "zip": "13700",
                "city": "Tomelloso",
                "state_id": self.state.id,
                "country_id": self.env.ref("base.es").id,
                "vat": "ES05680675C",
                "facturae": False,
                "attach_invoice_as_annex": False,
                "organo_gestor": "U00000038",
                "unidad_tramitadora": "U00000038",
                "oficina_contable": "U00000038",
            }
        )
        move_no_facturae = self.env["account.move"].create(
            {
                "partner_id": partner_no_facturae.id,
                "company_id": self.env.ref("base.main_company").id,
                "journal_id": self.sale_journal.id,
                "invoice_date": "2016-03-12",
                "payment_mode_id": self.payment_mode.id,
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
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
        move_no_facturae.action_post()
        with self.assertRaises(exceptions.ValidationError):
            self.wizard.with_context(
                active_ids=move_no_facturae.ids,
                active_model="account.move",
                skip_signature=True,
            ).create_facturae_file()

    def test_move_without_taxes(self):
        move_no_taxes = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "company_id": self.env.ref("base.main_company").id,
                "journal_id": self.sale_journal.id,
                "invoice_date": "2016-03-12",
                "payment_mode_id": self.payment_mode.id,
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "account_id": self.account.id,
                            "name": "Producto de prueba",
                            "quantity": 1.0,
                            "price_unit": 100.0,
                            "tax_ids": False,
                        },
                    )
                ],
            }
        )
        move_no_taxes.action_post()
        with self.assertRaises(exceptions.ValidationError):
            self.wizard.with_context(
                active_ids=move_no_taxes.ids,
                active_model="account.move",
                skip_signature=True,
            ).create_facturae_file()

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
                "company_id": self.env.ref("base.main_company").id,
                "journal_id": self.sale_journal.id,
                "invoice_date": "2016-03-12",
                "payment_mode_id": self.payment_mode.id,
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
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
