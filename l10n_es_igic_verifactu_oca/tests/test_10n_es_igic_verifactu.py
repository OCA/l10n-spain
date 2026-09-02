# Copyright 2025 Binhex - Christian Ramos
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from odoo.exceptions import UserError

from odoo.addons.l10n_es_verifactu_oca.tests.test_10n_es_verifactu import (
    TestL10nEsAeatVerifactu,
)

from .common import TestVerifactuIgicCommon


class TestL10nEsAeatVerifactuIgicMixin(TestVerifactuIgicCommon):
    # This function override is needed because the company id is dynamic
    # so if we introduce the hole tax xmlid it will fail in finding the
    # JSON file like l10n_es_igic.3_account_tax_template_igic_r_3
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
                    xml_id = "l10n_es_igic.{}_account_tax_template_{}".format(
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
        return TestL10nEsAeatVerifactu._compare_verifactu_dict(
            self, json_file, name, inv_type, lines, extra_vals, module
        )


class TestL10nEsAeatVerifactuIgicNewTaxes(TestL10nEsAeatVerifactuIgicMixin):
    def test_get_verifactu_igic_cmino(self):
        """Minorista: igic_cmino en línea + IGIC teórico en producto (igic_r_7)."""
        cmino = self.env.ref(
            f"l10n_es_igic.{self.company.id}_account_tax_template_igic_cmino"
        )
        self._compare_verifactu_dict(
            "verifactu_out_invoice_igic_cmino_dict.json",
            "TEST003",
            "out_invoice",
            [{"price_unit": 100, "taxes": cmino}],
            {
                "fiscal_position_id": self.fp_retailer.id,
                "verifactu_registration_key": self.fp_registration_key_17.id,
                "verifactu_registration_date": "2026-01-01 19:20:30",
            },
            "l10n_es_igic_verifactu_oca",
        )

    def test_get_verifactu_igic_minorista_r_3(self):
        cmino = self.env.ref(
            f"l10n_es_igic.{self.company.id}_account_tax_template_igic_cmino"
        )
        self.product.taxes_id = [(6, 0, [self.tax_igic_r_3.id])]
        self._compare_verifactu_dict(
            "verifactu_out_invoice_igic_r_3_dict.json",
            "TEST005",
            "out_invoice",
            [{"price_unit": 100, "taxes": cmino}],
            {
                "fiscal_position_id": self.fp_retailer.id,
                "verifactu_registration_key": self.fp_registration_key_17.id,
                "verifactu_registration_date": "2026-01-01 19:20:30",
            },
            "l10n_es_igic_verifactu_oca",
        )

    def test_get_verifactu_igic_minorista_missing_theoretical_rate(self):
        from odoo import Command

        product = self.env["product.product"].create({"name": "No IGIC tax"})
        cmino = self.env.ref(
            f"l10n_es_igic.{self.company.id}_account_tax_template_igic_cmino"
        )
        invoice = self.env["account.move"].create(
            {
                "name": "TEST006",
                "partner_id": self.partner.id,
                "invoice_date": "2026-01-01",
                "move_type": "out_invoice",
                "fiscal_position_id": self.fp_retailer.id,
                "verifactu_registration_key": self.fp_registration_key_17.id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": product.id,
                            "account_id": self.account_expense.id,
                            "name": "Test line",
                            "price_unit": 100,
                            "quantity": 1,
                            "tax_ids": [Command.set(cmino.ids)],
                        }
                    )
                ],
            }
        )
        with self.assertRaises(UserError):
            invoice._get_verifactu_invoice_dict_out()

    def test_get_verifactu_igic_r_1(self):
        self._create_and_test_invoice_verifactu_dict(
            "TEST004",
            "out_invoice",
            [(100, ["igic_r_1"])],
            {
                "fiscal_position_id": self.fp_nacional.id,
                "verifactu_registration_key": self.fp_registration_key_01.id,
                "verifactu_registration_date": "2026-01-01 19:20:30",
            },
            "l10n_es_igic_verifactu_oca",
        )


class TestL10nEsAeatVerifactuIgic(TestL10nEsAeatVerifactuIgicMixin):
    def test_verifactu_hash_code(self):
        TestL10nEsAeatVerifactu.test_verifactu_hash_code(self)

    def test_get_verifactu_invoice_data(self):
        mapping = [
            (
                "TEST001",
                "out_invoice",
                [(100, ["igic_r_3"]), (200, ["igic_r_7"])],
                {
                    "fiscal_position_id": self.fp_nacional.id,
                    "verifactu_registration_key": self.fp_registration_key_01.id,
                    "verifactu_registration_date": "2026-01-01 19:20:30",
                },
            ),
            (
                "TEST002",
                "out_refund",
                [(100, ["igic_r_3"]), (100, ["igic_r_3"]), (200, ["igic_r_7"])],
                {
                    "fiscal_position_id": self.fp_nacional.id,
                    "verifactu_registration_key": self.fp_registration_key_01.id,
                    "verifactu_registration_date": "2026-01-01 19:20:30",
                },
            ),
        ]
        for name, inv_type, lines, extra_vals in mapping:
            self._create_and_test_invoice_verifactu_dict(
                name, inv_type, lines, extra_vals, "l10n_es_igic_verifactu_oca"
            )
        return

    def test_verifactu_start_date(self):
        TestL10nEsAeatVerifactu.test_verifactu_start_date(self)
