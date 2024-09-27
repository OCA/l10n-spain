# Copyright 2017 FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# Copyright 2017-2021 Tecnativa - Pedro M. Baeza
# Copyright 2018 PESOL - Angel Moya <angel.moya@pesol.es>
# Copyright 2020 Valentin Vinagre <valent.vinagre@sygel.es>
# Copyright 2021 Tecnativa - João Marques
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import json

from odoo import exceptions
from odoo.modules.module import get_resource_path

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
                if "." in tax:
                    xml_id = tax
                else:
                    xml_id = "l10n_es.{}_account_tax_template_{}".format(
                        self.company.id, tax
                    )
                taxes += self.env.ref(xml_id)
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
        vals = {
            "name": "TEST001",
            "partner_id": self.partner.id,
            "invoice_date": "2020-01-01",
            "move_type": inv_type,
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
        result_dict = invoice._get_sii_invoice_dict()
        path = get_resource_path(module, "tests/json", json_file)
        if not path:
            raise Exception("Incorrect JSON file: %s" % json_file)
        with open(path, "r") as f:
            expected_dict = json.loads(f.read())
        self.assertEqual(expected_dict, result_dict)
        return invoice

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
            "l10n_es.%s_account_common_600" % cls.company.id
        )
        cls.invoice = cls.env["account.move"].create(
            {
                "company_id": cls.company.id,
                "partner_id": cls.partner.id,
                "invoice_date": "2018-02-01",
                "move_type": "out_invoice",
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
        cls.company.write(
            {
                "sii_enabled": True,
                "sii_test": True,
                "use_connector": True,
                "vat": "ESU2687761C",
                "sii_description_method": "manual",
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
        cls.tax_agencies = cls.env["aeat.sii.tax.agency"].search([])

    def test_job_creation(self):
        self.assertTrue(self.invoice.invoice_jobs_ids)

    def test_get_invoice_data(self):
        mapping = [
            ("out_invoice", [(100, ["s_iva10b"]), (200, ["s_iva21s"])], {}),
            ("out_invoice", [(100, ["s_iva10b"]), (200, ["s_iva0_ns"])], {}),
            (
                "out_invoice",
                [(100, ["s_iva10b", "s_req014"]), (200, ["s_iva21s", "s_req52"])],
                {},
            ),
            (
                "out_refund",
                [(100, ["s_iva10b"]), (100, ["s_iva10b"]), (200, ["s_iva21s"])],
                {},
            ),
            ("out_invoice", [(100, ["s_iva0_sp_i"]), (200, ["s_iva0_ic"])], {}),
            ("out_refund", [(100, ["s_iva0_sp_i"]), (200, ["s_iva0_ic"])], {}),
            ("out_invoice", [(100, ["s_iva_e"]), (200, ["s_iva0_e"])], {}),
            ("out_refund", [(100, ["s_iva_e"]), (200, ["s_iva0_e"])], {}),
            (
                "in_invoice",
                [(100, ["p_iva10_bc", "p_irpf19"]), (200, ["p_iva21_sc", "p_irpf19"])],
                {
                    "ref": "sup0001",
                    "date": "2020-02-01",
                    "sii_account_registration_date": "2020-10-01",
                },
            ),
            (
                "in_refund",
                [(100, ["p_iva10_bc"])],
                {"ref": "sup0002", "sii_account_registration_date": "2020-10-01"},
            ),
            (
                "in_invoice",
                [(100, ["p_iva10_bc", "p_req014"]), (200, ["p_iva21_sc", "p_req52"])],
                {"ref": "sup0003", "sii_account_registration_date": "2020-10-01"},
            ),
            (
                "in_invoice",
                [(100, ["p_iva21_sp_ex"])],
                {"ref": "sup0004", "sii_account_registration_date": "2020-10-01"},
            ),
            (
                "in_invoice",
                [(100, ["p_iva0_ns"]), (200, ["p_iva10_bc"])],
                {"ref": "sup0005", "sii_account_registration_date": "2020-10-01"},
            ),
            # Out invoice with currency
            ("out_invoice", [(100, ["s_iva10b"])], {"currency_id": self.usd.id}),
            # Out invoice with currency and with not included in total amount
            (
                "out_invoice",
                [(100, ["s_iva10b", "s_irpf1"])],
                {"currency_id": self.usd.id},
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
            ),
            # Intra-community supplier refund with ImporteTotal with "one side"
            (
                "in_refund",
                [(100, ["p_iva21_sp_in"])],
                {"ref": "sup0008", "sii_account_registration_date": "2020-10-01"},
            ),
        ]
        for inv_type, lines, extra_vals in mapping:
            self._create_and_test_invoice_sii_dict(inv_type, lines, extra_vals)
        return

    def test_action_cancel(self):
        self.invoice.invoice_jobs_ids.state = "started"
        with self.assertRaises(exceptions.UserError):
            self.invoice.button_cancel()

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
        invoice_temp = self.invoice.copy()
        # FIXME: Can we auto-trigger the compute method?
        invoice_temp._compute_sii_description()
        self.assertEqual(
            invoice_temp.sii_description,
            "Test customer header | Test description",
        )
        invoice_temp = self.invoice.copy(
            {"move_type": "in_invoice", "journal_id": self.journal_purchase.id}
        )
        invoice_temp._compute_sii_description()
        self.assertEqual(
            invoice_temp.sii_description,
            "Test supplier header | Test description",
        )
        company.sii_description = False
        company.sii_description_method = "manual"
        invoice_temp = self.invoice.copy()
        invoice_temp._compute_sii_description()
        self.assertEqual(invoice_temp.sii_description, "Test customer header")
        invoice_temp.sii_description = "Other thing"
        self.assertEqual(invoice_temp.sii_description, "Other thing")
        company.sii_description_method = "auto"
        invoice_temp = self.invoice.copy()
        invoice_temp._compute_sii_description()
        self.assertEqual(
            invoice_temp.sii_description,
            "Test customer header | Test line",
        )

    def _check_binding_address(self, invoice):
        company = invoice.company_id
        tax_agency = company.sii_tax_agency_id
        self.sii_cert.company_id.sii_tax_agency_id = tax_agency
        proxy = invoice._connect_sii(invoice.move_type)
        address = proxy._binding_options["address"]
        self.assertTrue(address)
        if company.sii_test and tax_agency:
            params = tax_agency._connect_params_sii(invoice.move_type, company)
            if params["address"]:
                self.assertEqual(address, params["address"])

    def _check_tax_agencies(self, invoice):
        for tax_agency in self.tax_agencies:
            invoice.company_id.sii_tax_agency_id = tax_agency
            self._check_binding_address(invoice)
        else:
            invoice.company_id.sii_tax_agency_id = False
            self._check_binding_address(invoice)

    def test_tax_agencies_sandbox(self):
        self.sii_cert.company_id = self.invoice.company_id.id
        self._activate_certificate()
        self.invoice.company_id.sii_test = True
        self._check_tax_agencies(self.invoice)
        in_invoice = self.invoice.copy(
            {"move_type": "in_invoice", "journal_id": self.journal_purchase.id}
        )
        self._check_tax_agencies(in_invoice)

    def test_tax_agencies_production(self):
        self.sii_cert.company_id = self.invoice.company_id.id
        self._activate_certificate()
        self.invoice.company_id.sii_test = False
        self._check_tax_agencies(self.invoice)
        in_invoice = self.invoice.copy(
            {"move_type": "in_invoice", "journal_id": self.journal_purchase.id}
        )
        self._check_tax_agencies(in_invoice)

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

    def test_is_sii_simplified_invoice(self):
        self.assertFalse(self.invoice._is_sii_simplified_invoice())
        self.partner.sii_simplified_invoice = True
        self.assertTrue(self.invoice._is_sii_simplified_invoice())

    def test_sii_check_exceptions_case_supplier_simplified(self):
        self.partner.sii_simplified_invoice = True
        invoice = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "invoice_date": "2018-02-01",
                "move_type": "in_invoice",
            }
        )
        with self.assertRaises(exceptions.UserError):
            invoice._sii_check_exceptions()

    def test_unlink_invoice_when_sent_to_sii(self):
        self.invoice.sii_state = "sent"
        with self.assertRaises(exceptions.UserError):
            self.invoice.unlink()
