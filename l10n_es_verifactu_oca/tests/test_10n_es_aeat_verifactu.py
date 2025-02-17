# Copyright 2024 Aures TIC - Almudena de La Puente <almudena@aurestic.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import json
from hashlib import sha256
from urllib.parse import parse_qs, urlparse

from odoo.modules.module import get_resource_path

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_certificate import (
    TestL10nEsAeatCertificateBase,
)
from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)


class TestL10nEsAeatVerifactuBase(TestL10nEsAeatModBase, TestL10nEsAeatCertificateBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.maxDiff = None
        cls.fp_nacional = cls.env.ref(f"l10n_es.{cls.company.id}_fp_nacional")
        cls.fp_registration_key_01 = cls.env.ref(
            "l10n_es_aeat_verifactu.aeat_verifactu_registration_keys_01"
        )
        cls.fp_nacional.verifactu_registration_key = cls.fp_registration_key_01
        cls.fp_recargo = cls.env.ref(f"l10n_es.{cls.company.id}_fp_recargo")
        cls.fp_recargo.verifactu_registration_key = cls.fp_registration_key_01
        cls.partner = cls.env["res.partner"].create(
            {"name": "Test partner", "vat": "89890001K"}
        )
        cls.product = cls.env["product.product"].create({"name": "Test product"})
        cls.account_expense = cls.env.ref(
            "l10n_es.%s_account_common_600" % cls.company.id
        )
        cls.invoice = cls.env["account.move"].create(
            {
                "company_id": cls.company.id,
                "partner_id": cls.partner.id,
                "invoice_date": "2024-01-01",
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
                "verifactu_enabled": True,
                "verifactu_test": True,
                "vat": "G87846952",
                "tax_agency_id": cls.env.ref("l10n_es_aeat.aeat_tax_agency_spain"),
            }
        )

    def test_verifactu_hash_code(self):
        # based on AEAT Verifactu documentation
        # https://www.agenciatributaria.es/static_files/AEAT_Desarrolladores/EEDD/IVA/VERI-FACTU/Veri-Factu_especificaciones_huella_hash_registros.pdf  # noqa: B950
        expected_hash = (
            "3C464DAF61ACB827C65FDA19F352A4E3BDC2C640E9E9FC4CC058073F38F12F60"
        )
        issuerID = "89890001K"
        serialNumber = "12345678/G33"
        expeditionDate = "01-01-2024"
        documentType = "F1"
        amountTax = "12.35"
        amountTotal = "123.45"
        previousHash = ""
        registrationDate = "2024-01-01T19:20:30+01:00"
        verifactu_hash_string = (
            f"IDEmisorFactura={issuerID}&"
            f"NumSerieFactura={serialNumber}&"
            f"FechaExpedicionFactura={expeditionDate}&"
            f"TipoFactura={documentType}&"
            f"CuotaTotal={amountTax}&"
            f"ImporteTotal={amountTotal}&"
            f"Huella={previousHash}&"
            f"FechaHoraHusoGenRegistro={registrationDate}"
        )
        sha_hash_code = sha256(verifactu_hash_string.encode("utf-8"))
        hash_code = sha_hash_code.hexdigest().upper()
        self.assertEqual(hash_code, expected_hash)

    def _create_and_test_invoice_verifactu_dict(
        self, name, inv_type, lines, extra_vals, module=None
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
        return self._compare_verifactu_dict(
            "verifactu_{}_{}_dict.json".format(inv_type, "_".join(tax_names)),
            name,
            inv_type,
            vals,
            extra_vals=extra_vals,
            module=module,
        )

    def _compare_verifactu_dict(
        self, json_file, name, inv_type, lines, extra_vals=None, module=None
    ):
        """Helper method for creating an invoice according arguments, and
        comparing the expected verifactu dict with .
        """
        module = module or "l10n_es_aeat_verifactu"
        vals = {
            "name": name,
            "partner_id": self.partner.id,
            "invoice_date": "2024-01-01",
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
        invoice.action_post()
        result_dict = invoice._get_verifactu_invoice_dict()
        result_dict["RegistroAlta"].pop("FechaHoraHusoGenRegistro")
        result_dict["RegistroAlta"].pop("TipoHuella")
        result_dict["RegistroAlta"].pop("Huella")
        path = get_resource_path(module, "tests/json", json_file)
        if not path:
            raise Exception("Incorrect JSON file: %s" % json_file)
        with open(path, "r") as f:
            expected_dict = json.loads(f.read())
        self.assertEqual(expected_dict, result_dict)
        return invoice


class TestL10nEsAeatVerifactu(TestL10nEsAeatVerifactuBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_get_verifactu_invoice_data(self):
        mapping = [
            (
                "TEST001",
                "out_invoice",
                [(100, ["s_iva10b"]), (200, ["s_iva21s"])],
                {
                    "fiscal_position_id": self.fp_nacional.id,
                    "verifactu_registration_key": self.fp_registration_key_01.id,
                },
            ),
            (
                "TEST002",
                "out_refund",
                [(100, ["s_iva10b"]), (100, ["s_iva10b"]), (200, ["s_iva21s"])],
                {
                    "fiscal_position_id": self.fp_nacional.id,
                    "verifactu_registration_key": self.fp_registration_key_01.id,
                },
            ),
            (
                "TEST003",
                "out_invoice",
                [(200, ["s_iva21s", "s_req52"])],
                {
                    "fiscal_position_id": self.fp_recargo.id,
                    "verifactu_registration_key": self.fp_registration_key_01.id,
                },
            ),
        ]
        for name, inv_type, lines, extra_vals in mapping:
            self._create_and_test_invoice_verifactu_dict(
                name, inv_type, lines, extra_vals
            )
        return


class TestL10nEsAeatVerifactuQR(TestL10nEsAeatVerifactuBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def _get_required_qr_params(self):
        """Helper to generate the required QR code parameters."""
        return {
            "nif": self.invoice.company_id.partner_id._parse_aeat_vat_info()[2],
            "numserie": self.invoice.name,
            "fecha": self.invoice._change_date_format(self.invoice.invoice_date),
            "importe": self.invoice.amount_total,
        }

    def test_verifactu_qr_generation(self):
        """
        Test the generation of the QR code image for the invoice.
        """
        self.invoice.action_post()
        qr_code = self.invoice.verifactu_qr

        self.assertTrue(qr_code, "QR code should be generated for the invoice.")
        self.assertIsInstance(qr_code, bytes, "QR code should be in bytes format.")

    def test_verifactu_qr_url_format(self):
        """
        Test the format of the generated QR URL to ensure it meets expected criteria.
        """
        self.invoice.action_post()
        qr_url = self.invoice.verifactu_qr_url

        self.assertTrue(qr_url, "QR URL should be generated for the invoice.")

        test_url = self.env.ref(
            "l10n_es_aeat.aeat_tax_agency_spain"
        ).verifactu_qr_base_url_test_address
        self.assertTrue(test_url, "Test URL should not be empty.")

        parsed_url = urlparse(qr_url)
        actual_params = parse_qs(parsed_url.query)

        expected_params = self._get_required_qr_params()
        for key, expected_value in expected_params.items():
            self.assertIn(
                key, actual_params, f"QR URL should contain the parameter: {key}"
            )
            self.assertEqual(
                actual_params[key][0],
                str(expected_value),
                f"QR URL parameter '{key}' should have value '{expected_value}', "
                "got '{actual_params[key][0]}' instead.",
            )

    def test_verifactu_qr_code_generation_on_draft(self):
        """
        Ensure that the QR code is not generated for invoices in draft state.
        """
        qr_code = self.invoice.verifactu_qr
        self.assertFalse(qr_code, "QR code should not be generated for draft invoices.")

    def test_verifactu_qr_code_after_update(self):
        """
        Test that the QR code is regenerated if the invoice details are updated.
        """
        self.invoice.action_post()
        original_qr_code = self.invoice.verifactu_qr

        self.invoice.button_cancel()

        self.invoice.button_draft()

        self.invoice.write(
            {
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "account_id": self.account_expense.id,
                            "name": "Updated line",
                            "price_unit": 200,
                            "quantity": 1,
                        },
                    )
                ]
            }
        )
        self.invoice.action_post()

        self.invoice.invalidate_model(["verifactu_qr_url", "verifactu_qr"])

        updated_qr_code = self.invoice.verifactu_qr

        self.assertNotEqual(
            original_qr_code,
            updated_qr_code,
            "QR code should be regenerated after invoice update.",
        )
