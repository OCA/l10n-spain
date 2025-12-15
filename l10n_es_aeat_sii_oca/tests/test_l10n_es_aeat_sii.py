# Copyright 2017 FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# Copyright 2018 PESOL - Angel Moya <angel.moya@pesol.es>
# Copyright 2020 Valentin Vinagre <valent.vinagre@sygel.es>
# Copyright 2021 Tecnativa - João Marques
# Copyright 2017-2023 Tecnativa - Pedro M. Baeza
# Copyright 2023 Moduon Team - Eduardo de Miguel
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import json

from odoo import exceptions
from odoo.tools.misc import file_path

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_certificate import (
    TestL10nEsAeatCertificateBase,
)
from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)


class TestL10nEsAeatSiiBase(TestL10nEsAeatModBase, TestL10nEsAeatCertificateBase):
    @classmethod
    def _get_or_create_tax(cls, xml_id, name, tax_type, percentage, extra_vals=None):
        """Helper for quick-creating a tax with an specific XML-ID"""
        tax = cls.env.ref("l10n_es." + xml_id, raise_if_not_found=False)
        if not tax:
            vals = {
                "name": name,
                "type_tax_use": tax_type,
                "amount_type": "percent",
                "amount": percentage,
            }
            if extra_vals:
                vals.update(extra_vals)
            tax = cls.env["account.tax"].create(vals)
            cls.env["ir.model.data"].create(
                {
                    "module": "l10n_es",
                    "name": xml_id,
                    "model": tax._name,
                    "res_id": tax.id,
                }
            )
        return tax

    def _create_and_test_invoice_sii_dict(
        self, inv_type, lines, extra_vals, module=None
    ):
        vals = []
        tax_names = []
        for line in lines:
            taxes = self.env["account.tax"]
            for tax in line[1]:
                xml_id = f"account_tax_template_{tax}"
                tax_id = self.company._get_tax_id_from_xmlid(xml_id)
                taxes += self.env["account.tax"].browse(tax_id)
                tax_names.append(tax)
            vals.append({"price_unit": line[0], "taxes": taxes})
        return self._compare_sii_dict(
            "sii_{}_{}_dict.json".format(inv_type, "_".join(tax_names)),
            inv_type,
            vals,
            extra_vals=extra_vals,
            module=module,
        )

    def _compare_sii_dict(
        self, json_file, inv_type, lines, extra_vals=None, module=None
    ):
        """Helper method for creating an invoice according arguments, and
        comparing the expected SII dict with .
        """
        module = module or "l10n_es_aeat_sii_oca"
        domain = [
            ("code", "=", "01"),
            ("type", "=", "sale" if "out" in inv_type else "purchase"),
        ]
        sii_key_obj = self.env["aeat.sii.mapping.registration.keys"]
        vals = {
            "name": "TEST001",
            "partner_id": self.partner.id,
            "invoice_date": "2020-01-01",
            "move_type": inv_type,
            # FIXME: This should be auto-assigned, but not working due to unknown glitch
            "sii_registration_key": sii_key_obj.search(domain, limit=1).id,
            "invoice_line_ids": [],
        }
        for line in lines:
            vals["invoice_line_ids"].append(
                (
                    0,
                    0,
                    {
                        "product_id": self.product.id,
                        "account_id": self.account_expense.id,
                        "name": "Test line",
                        "price_unit": line["price_unit"],
                        "quantity": 1,
                        "tax_ids": [(6, 0, line["taxes"].ids)],
                    },
                )
            )
        if extra_vals:
            vals.update(extra_vals)
        invoice = self.env["account.move"].create(vals)
        result_dict = invoice._get_aeat_invoice_dict()
        path = file_path(f"{module}/tests/json/{json_file}")
        if not path:
            raise Exception("Incorrect JSON file: %s" % json_file)
        with open(path) as f:
            expected_dict = json.loads(f.read())
        self.assertEqual(expected_dict, result_dict)
        return invoice

    @classmethod
    def _create_invoice(cls, move_type):
        return cls.env["account.move"].create(
            {
                "company_id": cls.company.id,
                "partner_id": cls.partner.id,
                "invoice_date": "2018-02-01",
                "move_type": move_type,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product.id,
                            "account_id": cls.account_expense.id,
                            "name": "Test line",
                            "price_unit": 100,
                            "quantity": 1,
                        },
                    )
                ],
            }
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.maxDiff = None  # needed for the dict comparison
        cls.partner = cls.env["res.partner"].create(
            {"name": "Test partner", "vat": "ESF35999705"}
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Test product", "sii_exempt_cause": "E5"}
        )
        cls.account_expense = cls.env.ref(
            "account.%s_account_common_600" % cls.company.id
        )
        cls.invoice = cls._create_invoice("out_invoice")
        cls.company.write(
            {
                "sii_enabled": True,
                "sii_test": True,
                "vat": "ESU2687761C",
                "sii_description_method": "manual",
                "tax_agency_id": cls.env.ref("l10n_es_aeat.aeat_tax_agency_spain"),
            }
        )


class TestL10nEsAeatSii(TestL10nEsAeatSiiBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.invoice.action_post()
        cls.invoice.name = "INV001"
        cls.invoice.refund_invoice_ids = cls.invoice.copy()
        cls.user = cls.env["res.users"].create(
            {
                "name": "Test user",
                "login": "test_user",
                "groups_id": [(4, cls.env.ref("account.group_account_invoice").id)],
                "email": "somebody@somewhere.com",
            }
        )
        cls.tax_agencies = cls.env["aeat.tax.agency"].search(
            [("sii_wsdl_out", "!=", False)]
        )

    def test_invoice_search_sii_enabled(self):
        domain_base = [("id", "=", self.invoice.id)]
        domain_ok = domain_base + [("sii_enabled", "=", True)]
        items = self.env["account.move"].search(domain_ok)
        self.assertIn(self.invoice, items)
        domain_ko_1 = domain_base + [("sii_enabled", "=", False)]
        items = self.env["account.move"].search(domain_ko_1)
        self.assertNotIn(self.invoice, items)
        domain_ko_2 = domain_base + [("sii_enabled", "!=", True)]
        items = self.env["account.move"].search(domain_ko_2)
        self.assertNotIn(self.invoice, items)
        self.invoice.journal_id.sii_enabled = False
        items = self.env["account.move"].search(domain_ok)
        self.assertNotIn(self.invoice, items)
        items = self.env["account.move"].search(domain_ko_1)
        self.assertIn(self.invoice, items)
        items = self.env["account.move"].search(domain_ko_2)
        self.assertIn(self.invoice, items)

    def test_intracomunitary_customer_extracomunitary_delivery(self):
        """Comprobar venta a un cliente intracomunitario enviada al extranjero.

        Este caso se puede dar cuando una asesoría contable contabiliza facturas
        para otro cliente, en caso de que ese cliente le venda a otro cliente
        intracomunitario pero envíe a una dirección extracomunitaria.

        También se puede dar cuando se instala el módulo `sale` en Odoo. Al instalarlo,
        se añade el campo `partner_shipping_id`, que permite indicar una dirección
        de entrega extracomunitaria para clientes intracomunitarios.
        """
        self._activate_certificate(self.certificate_password)
        eu_customer = self.env["res.partner"].create(
            {
                "name": "French Customer",
                "country_id": self.ref("base.fr"),
                "vat": "FR23334175221",
            }
        )
        fp_extra = self.browse_ref(f"account.{self.company.id}_fp_extra")
        fp_extra.sii_partner_identification_type = "3"
        invoice = self.invoice.copy(
            {"partner_id": eu_customer.id, "fiscal_position_id": fp_extra.id}
        )
        invoice.action_post()
        sii_info = invoice._get_aeat_invoice_dict()
        self.assertEqual(
            sii_info["FacturaExpedida"]["Contraparte"],
            {
                "NombreRazon": "French Customer",
                "IDOtro": {"CodigoPais": "FR", "IDType": "06", "ID": "23334175221"},
            },
        )

    def test_partner_sii_enabled(self):
        company_02 = self.env["res.company"].create({"name": "Company 02"})
        self.env.user.company_ids += company_02
        self.assertTrue(self.partner.sii_enabled)
        self.partner.company_id = company_02
        self.assertFalse(self.partner.sii_enabled)

    def test_get_invoice_data(self):
        mapping = [
            ("out_invoice", [(100, ["s_iva10b"]), (200, ["s_iva21s"])], {}, False),
            ("out_invoice", [(100, ["s_iva10b"]), (200, ["s_iva0_ns"])], {}, False),
            (
                "out_invoice",
                [(100, ["s_iva10b", "s_req014"]), (200, ["s_iva21s", "s_req52"])],
                {},
                False,
            ),
            (
                "out_refund",
                [(100, ["s_iva10b"]), (100, ["s_iva10b"]), (200, ["s_iva21s"])],
                {},
                False,
            ),
            ("out_invoice", [(100, ["s_iva0_sp_i"]), (200, ["s_iva0_g_i"])], {}, False),
            ("out_refund", [(100, ["s_iva0_sp_i"]), (200, ["s_iva0_g_i"])], {}, False),
            ("out_invoice", [(100, ["s_iva_e"]), (200, ["s_iva0_g_e"])], {}, False),
            ("out_refund", [(100, ["s_iva_e"]), (200, ["s_iva0_g_e"])], {}, False),
            (
                "in_invoice",
                [(100, ["p_iva10_bc", "p_irpf19"]), (200, ["p_iva21_sc", "p_irpf19"])],
                {
                    "ref": "sup0001",
                    "date": "2020-02-01",
                    "sii_account_registration_date": "2020-10-01",
                },
                False,
            ),
            (
                "in_refund",
                [(100, ["p_iva10_bc"])],
                {"ref": "sup0002", "sii_account_registration_date": "2020-10-01"},
                False,
            ),
            (
                "in_invoice",
                [(100, ["p_iva10_bc", "p_req014"]), (200, ["p_iva21_sc", "p_req52"])],
                {"ref": "sup0003", "sii_account_registration_date": "2020-10-01"},
                False,
            ),
            (
                "in_invoice",
                [(100, ["p_iva21_sp_ex"])],
                {"ref": "sup0004", "sii_account_registration_date": "2020-10-01"},
                False,
            ),
            (
                "in_invoice",
                [(100, ["p_iva0_ns"]), (200, ["p_iva10_bc"])],
                {"ref": "sup0005", "sii_account_registration_date": "2020-10-01"},
                False,
            ),
            # Out invoice with currency
            ("out_invoice", [(100, ["s_iva10b"])], {"currency_id": self.usd.id}, False),
            # Out invoice with currency and with not included in total amount
            (
                "out_invoice",
                [(100, ["s_iva10b", "s_irpf1"])],
                {"currency_id": self.usd.id},
                False,
            ),
            # In invoice with currency
            (
                "in_invoice",
                [(100, ["p_iva10_bc"])],
                {
                    "ref": "sup0006",
                    "sii_account_registration_date": "2020-10-01",
                    "currency_id": self.usd.id,
                },
                False,
            ),
            # In invoice with currency and with not included in total amount
            (
                "in_invoice",
                [(100, ["p_iva10_bc", "p_irpf1"])],
                {
                    "ref": "sup0007",
                    "sii_account_registration_date": "2020-10-01",
                    "currency_id": self.usd.id,
                },
                False,
            ),
            # Intra-community supplier refund with ImporteTotal with "one side"
            (
                "in_refund",
                [(100, ["p_iva21_sp_in"])],
                {"ref": "sup0008", "sii_account_registration_date": "2020-10-01"},
                False,
            ),
            (
                "in_invoice",
                [(100, ["p_iva21_ibc_group"])],
                {
                    "ref": "sup0001",
                    "sii_account_registration_date": "2020-10-01",
                    "currency_id": self.usd.id,
                },
                True,
            ),
        ]
        for inv_type, lines, extra_vals, is_dua in mapping:
            invoice = self._create_and_test_invoice_sii_dict(
                inv_type, lines, extra_vals
            )
            if is_dua:
                self.assertTrue(invoice.sii_dua_invoice)
            else:
                self.assertFalse(invoice.sii_dua_invoice)
        return

    def test_sii_description(self):
        company = self.invoice.company_id
        company.write(
            {
                "sii_header_customer": "Test customer header",
                "sii_header_supplier": "Test supplier header",
                "sii_description": " | Test description",
                "sii_description_method": "fixed",
            }
        )
        self.invoice._compute_sii_description()
        self.assertEqual(
            self.invoice.sii_description,
            "Test customer header | Test description",
        )
        invoice_temp = self._create_invoice("in_invoice")
        self.assertEqual(
            invoice_temp.sii_description,
            "Test supplier header | Test description",
        )
        company.sii_description = False
        company.sii_description_method = "manual"
        self.invoice.sii_description = "/"
        self.invoice._compute_sii_description()
        self.assertEqual(self.invoice.sii_description, "Test customer header")
        self.invoice.sii_description = "Other thing"
        self.assertEqual(self.invoice.sii_description, "Other thing")
        company.sii_description_method = "auto"
        self.invoice._compute_sii_description()
        self.assertEqual(
            self.invoice.sii_description,
            "Test customer header | Test line",
        )

    def test_vat_number_check(self):
        self.partner.write(
            {"vat": "F35999705", "country_id": self.env.ref("base.es").id}
        )
        # Repeat get invoice data tests to ensure no change is due to the VAT number
        # expressed without country, but setting the country
        self.test_get_invoice_data()

    def _check_binding_address(self, invoice):
        company = invoice.company_id
        tax_agency = company.tax_agency_id
        self.sii_cert.company_id.tax_agency_id = tax_agency
        proxy = invoice._connect_aeat(invoice.move_type)
        address = proxy._binding_options["address"]
        self.assertTrue(address)
        if company.sii_test and tax_agency:
            params = tax_agency._connect_params_sii(invoice.move_type, company)
            if params["address"]:
                self.assertEqual(address, params["address"])

    def _check_tax_agencies(self, invoice):
        for tax_agency in self.tax_agencies:
            invoice.company_id.tax_agency_id = tax_agency
            self._check_binding_address(invoice)
        else:
            invoice.company_id.tax_agency_id = False
            self._check_binding_address(invoice)

    def test_refund_sii_refund_type(self):
        invoice = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "invoice_date": "2018-02-01",
                "move_type": "out_refund",
            }
        )
        self.assertEqual(invoice.sii_refund_type, "I")

    def test_refund_sii_refund_type_write(self):
        invoice = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "invoice_date": "2018-02-01",
                "move_type": "out_invoice",
            }
        )
        self.assertFalse(invoice.sii_refund_type)
        invoice.move_type = "out_refund"
        self.assertEqual(invoice.sii_refund_type, "I")

    def test_is_aeat_simplified_invoice(self):
        self.assertFalse(self.invoice._is_aeat_simplified_invoice())
        self.partner.aeat_simplified_invoice = True
        self.assertTrue(self.invoice._is_aeat_simplified_invoice())

    def test_aeat_check_exceptions_case_supplier_simplified(self):
        self.partner.aeat_simplified_invoice = True
        invoice = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "invoice_date": "2018-02-01",
                "move_type": "in_invoice",
            }
        )
        with self.assertRaises(exceptions.UserError):
            invoice._aeat_check_exceptions()

    def test_aeat_check_exceptions_case_supplier_on_post(self):
        """Check sii exceptions when posting supplier bills"""
        supplier = self.supplier.copy()
        supplier.country_id = self.env.ref("base.es")
        supplier.vat = "A46180576"
        # Extra data without `ref` field
        extra_data_wo_ref = {
            "partner_id": supplier.id,
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "name": "Test line",
                        "account_id": self.accounts["600000"].id,
                        "price_unit": 100.0,
                        "quantity": 1,
                    },
                )
            ],
        }
        with self.assertRaises(exceptions.UserError):
            self._invoice_purchase_create("2018-02-01", extra_vals=extra_data_wo_ref)
        self.assertTrue(
            self._invoice_purchase_create(
                "2018-02-01", extra_vals=dict(extra_data_wo_ref, ref="TEST REF")
            )
        )

    def test_unlink_draft_invoice_when_not_sent_to_sii(self):
        draft_invoice = self.invoice.copy({})
        draft_invoice.unlink()
        self.assertFalse(draft_invoice.exists())

    def test_unlink_invoice_when_sent_to_sii(self):
        self.invoice.aeat_state = "sent"
        self.invoice.button_draft()  # Convert to draft to check only SII exception
        with self.assertRaises(exceptions.UserError):
            self.invoice.unlink()

    def test_account_move_sii_write_exceptions(self):
        # out_invoice
        self.invoice.aeat_state = "sent"
        with self.assertRaises(exceptions.UserError):
            self.invoice.write({"invoice_date": "2022-01-01"})
        with self.assertRaises(exceptions.UserError):
            self.invoice.write({"thirdparty_number": "CUSTOM"})
        # in_invoice
        in_invoice = self._create_invoice("in_invoice")
        in_invoice.ref = "REF"
        in_invoice.aeat_state = "sent"
        partner = self.partner.copy()
        with self.assertRaises(exceptions.UserError):
            in_invoice.write({"partner_id": partner.id})
        with self.assertRaises(exceptions.UserError):
            in_invoice.write({"ref": "REF2"})

    def test_account_move_reversal_out_invoice(self):
        reversal = (
            self.env["account.move.reversal"]
            .with_context(
                active_id=self.invoice.id,
                active_model=self.invoice._name,
                active_ids=self.invoice.ids,
            )
            .create(
                {
                    "journal_id": self.invoice.journal_id.id,
                }
            )
        )
        self.assertEqual(reversal.sii_refund_type, "I")
        self.assertTrue(reversal.sii_refund_type_required)
        self.assertFalse(reversal.supplier_invoice_number_refund_required)

    def test_dua_exempt_invoice(self):
        self.partner.write({"country_id": self.env.ref("base.us").id})
        invoice = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "invoice_date": "2018-02-01",
                "move_type": "in_invoice",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "name": "Test line",
                            "quantity": 1.0,
                            "price_unit": 100.00,
                        },
                    )
                ],
            }
        )
        self.assertFalse(invoice.sii_enabled)

    def test_send_sii_wizard(self):
        invoice = self._create_invoice("out_invoice")
        invoice_sii_failed = self._create_invoice("out_invoice")
        invoice_sii_modified = self._create_invoice("out_invoice")
        (invoice + invoice_sii_failed + invoice_sii_modified).action_post()
        (invoice + invoice_sii_failed + invoice_sii_modified).write(
            {"sii_send_date": False}
        )
        invoice_sii_failed.write({"aeat_send_failed": True})
        invoice_sii_modified.write({"aeat_state": "sent_modified"})
        wizard = (
            self.env["wizard.send.sii"]
            .with_context(
                active_model="account.move",
                active_ids=[invoice_sii_failed.id, invoice_sii_modified.id, invoice.id],
            )
            .create({})
        )
        self.assertEqual(wizard.not_send_without_errors_number, 1)
        self.assertEqual(wizard.with_errors_number, 1)
        self.assertEqual(wizard.modified_number, 1)
        self.assertFalse(invoice.sii_send_date)
        self.assertFalse(invoice_sii_failed.sii_send_date)
        self.assertFalse(invoice_sii_modified.sii_send_date)
        wizard.action_confirm()
        self.assertTrue(invoice.sii_send_date)
        self.assertTrue(invoice_sii_failed.sii_send_date)
        self.assertTrue(invoice_sii_modified.sii_send_date)

    def test_start_date(self):
        self.company.sii_start_date = "2018-01-01"
        invoice1 = self._create_invoice("out_invoice")
        invoice1.invoice_date = "2019-01-01"
        self.assertTrue(invoice1.sii_enabled)
        self.assertTrue(invoice1.filtered_domain([("sii_enabled", "=", True)]))
        invoice2 = self._create_invoice("out_invoice")
        invoice2.invoice_date = "2017-01-01"
        self.assertFalse(invoice2.sii_enabled)
        self.assertTrue(invoice2.filtered_domain([("sii_enabled", "=", False)]))
        self.company.sii_start_date = False
        self.assertTrue(invoice2.sii_enabled)
        self.assertTrue(invoice2.filtered_domain([("sii_enabled", "=", True)]))
