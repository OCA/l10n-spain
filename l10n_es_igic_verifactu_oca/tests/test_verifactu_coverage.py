# Copyright 2026 - OCA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from unittest.mock import patch

from odoo import Command
from odoo.exceptions import UserError

from .common import TestVerifactuIgicCommon


class TestVerifactuIgicCoverage(TestVerifactuIgicCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company.write(
            {
                "tax_agency_id": cls.env.ref(
                    "l10n_es_aeat.aeat_tax_agency_canarias"
                ).id,
                "verifactu_enabled": True,
                "verifactu_test": True,
            }
        )
        cls.cmino = cls.env.ref(
            f"l10n_es_igic.{cls.company.id}_account_tax_template_igic_cmino"
        )
        cls.tax_re_ex = cls.env.ref(
            f"l10n_es_igic.{cls.company.id}_account_tax_template_igic_re_ex"
        )
        cls.key_11 = cls.env.ref(
            "l10n_es_verifactu_oca.verifactu_registration_keys_igic_11"
        )

    def _invoice(self, taxes, product=None, fiscal_position=None, price=100):
        product = product if product is not None else self.product
        return self.env["account.move"].create(
            {
                "company_id": self.company.id,
                "partner_id": self.partner.id,
                "invoice_date": "2026-01-01",
                "move_type": "out_invoice",
                "fiscal_position_id": fiscal_position.id if fiscal_position else False,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": product.id,
                            "name": "Línea test",
                            "account_id": self.account_expense.id,
                            "price_unit": price,
                            "quantity": 1,
                            "tax_ids": [Command.set(taxes.ids)],
                        }
                    )
                ],
            }
        )

    def _tax_line(self, invoice, tax):
        for values in invoice._get_aeat_tax_info().values():
            if values["tax"] == tax:
                return values
        return None

    def _link_tax_to_map(self, tax, map_code, xml_name):
        template = self.env.ref("l10n_es_igic.account_tax_template_igic_r_0").copy(
            {"name": tax.name}
        )
        self.env["ir.model.data"].create(
            [
                {
                    "name": xml_name,
                    "module": "l10n_es_igic",
                    "model": "account.tax.template",
                    "res_id": template.id,
                },
                {
                    "name": f"{self.company.id}_{xml_name}",
                    "module": "l10n_es_igic",
                    "model": "account.tax",
                    "res_id": tax.id,
                },
            ]
        )
        map_line = self.env["verifactu.map.line"].search(
            [("code", "=", map_code)], limit=1
        )
        map_line.write({"taxes": [(4, template.id)]})
        self.env["res.company"].clear_caches()
        return tax

    def test_minorista_implicit_charge_when_operation_is_subject(self):
        invoice = self._invoice(self.cmino, fiscal_position=self.fp_retailer, price=100)
        invoice.verifactu_registration_key = self.fp_registration_key_17
        tax_line = self._tax_line(invoice, self.cmino)
        tax_dict = invoice._get_verifactu_tax_dict(tax_line, {}, "S1")
        self.assertEqual(tax_dict["TipoImpositivo"], "7.0")
        self.assertAlmostEqual(tax_dict["CargaImpositivaImplicitadeMinoristas"], 4.9)
        self.assertTrue(
            self.env["account.move"]._is_igic_minorista_sale_tax(self.cmino)
        )
        self.assertFalse(
            self.env["account.move"]._is_igic_minorista_sale_tax(self.tax_igic_r_7)
        )

    def test_minorista_subject_tax_is_not_rewritten(self):
        invoice = self._invoice(self.tax_igic_r_7, fiscal_position=self.fp_retailer)
        invoice.verifactu_registration_key = self.fp_registration_key_17
        tax_line = self._tax_line(invoice, self.tax_igic_r_7)
        tax_dict = invoice._get_verifactu_tax_dict(tax_line, {}, "S1")
        self.assertEqual(tax_dict["TipoImpositivo"], "7.0")
        self.assertNotIn("CargaImpositivaImplicitadeMinoristas", tax_dict)

    def test_minorista_without_cmino_group(self):
        original = type(self.env).ref

        def _ref(env, xml_id, raise_if_not_found=True):
            if xml_id == "l10n_es_igic.tax_group_igic_cmino":
                return env["account.tax.group"]
            return original(env, xml_id, raise_if_not_found)

        with patch.object(type(self.env), "ref", _ref):
            self.assertFalse(
                self.env["account.move"]._is_igic_minorista_sale_tax(self.cmino)
            )

    def test_minorista_theoretical_percent_errors(self):
        invoice = self._invoice(self.tax_igic_r_7)
        with self.assertRaises(UserError):
            invoice._get_igic_minorista_theoretical_percent(self.cmino)
        self.assertFalse(
            invoice._get_igic_theoretical_sale_taxes_from_product(
                self.env["product.product"]
            )
        )

        bare = self.env["product.product"].create({"name": "Sin IGIC"})
        invoice = self._invoice(self.cmino, product=bare, fiscal_position=False)
        line = invoice.invoice_line_ids
        self.assertIsNone(
            invoice._get_theoretical_percent_from_fp_mapping(line, self.cmino)
        )
        with self.assertRaises(UserError):
            invoice._get_igic_minorista_theoretical_percent(self.cmino)

        empty_fp = self.env["account.fiscal.position"].create(
            {"name": "Sin mapeo", "company_id": self.company.id}
        )
        invoice.fiscal_position_id = empty_fp
        self.assertIsNone(
            invoice._get_theoretical_percent_from_fp_mapping(line, self.cmino)
        )

        several = self.product.copy({"name": "Dos IGIC"})
        several.taxes_id = [(6, 0, (self.tax_igic_r_7 | self.tax_igic_r_3).ids)]
        invoice = self._invoice(self.cmino, product=several)
        with self.assertRaises(UserError):
            invoice._get_igic_minorista_theoretical_percent(self.cmino)

        other = self.tax_igic_r_7.copy({"name": "IGIC 4% suelto", "amount": 4})
        product = self.env["product.product"].create(
            {"name": "Tipo suelto", "taxes_id": [Command.set(other.ids)]}
        )
        invoice = self._invoice(
            self.cmino, product=product, fiscal_position=self.fp_retailer
        )
        self.assertIsNone(
            invoice._get_theoretical_percent_from_fp_mapping(
                invoice.invoice_line_ids, self.cmino
            )
        )
        with self.assertRaises(UserError):
            invoice._get_igic_minorista_theoretical_percent(self.cmino)

        product_r3 = self.env["product.product"].create(
            {"name": "IGIC 3", "taxes_id": [Command.set(self.tax_igic_r_3.ids)]}
        )
        invoice = self.env["account.move"].create(
            {
                "company_id": self.company.id,
                "partner_id": self.partner.id,
                "invoice_date": "2026-01-01",
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "name": "Siete",
                            "account_id": self.account_expense.id,
                            "price_unit": 100,
                            "quantity": 1,
                            "tax_ids": [Command.set(self.cmino.ids)],
                        }
                    ),
                    Command.create(
                        {
                            "product_id": product_r3.id,
                            "name": "Tres",
                            "account_id": self.account_expense.id,
                            "price_unit": 50,
                            "quantity": 1,
                            "tax_ids": [Command.set(self.cmino.ids)],
                        }
                    ),
                ],
            }
        )
        with self.assertRaises(UserError):
            invoice._get_igic_minorista_theoretical_percent(self.cmino)

    def test_minorista_percent_from_single_fp_mapping(self):
        product = self.env["product.product"].create({"name": "Sin impuesto"})
        fp = self.env["account.fiscal.position"].create(
            {
                "name": "Un mapeo",
                "company_id": self.company.id,
                "tax_ids": [
                    Command.create(
                        {
                            "tax_src_id": self.tax_igic_r_3.id,
                            "tax_dest_id": self.cmino.id,
                        }
                    )
                ],
            }
        )
        invoice = self._invoice(self.cmino, product=product, fiscal_position=fp)
        self.assertEqual(
            invoice._get_theoretical_percent_from_fp_mapping(
                invoice.invoice_line_ids, self.cmino
            ),
            3.0,
        )

    def test_minorista_percent_matches_product_tax(self):
        invoice = self._invoice(self.cmino, fiscal_position=self.fp_retailer, price=100)
        self.assertEqual(
            invoice._get_theoretical_percent_from_fp_mapping(
                invoice.invoice_line_ids, self.cmino
            ),
            7.0,
        )

    def test_missing_minorista_purchase_coefficient(self):
        invoice = self._invoice(self.cmino)
        with self.assertRaises(UserError):
            invoice._get_igic_minorista_implicit_coefficient(4)

    def test_missing_repep_and_export_taxes(self):
        invoice = self._invoice(self.tax_igic_r_7)
        original = type(self.env).ref

        def _ref(env, xml_id, raise_if_not_found=True):
            if xml_id.endswith(
                (
                    "_account_tax_template_igic_re_ex",
                    "_account_tax_template_igic_ex_0",
                )
            ):
                return env["account.tax"]
            return original(env, xml_id, raise_if_not_found)

        with patch.object(type(self.env), "ref", _ref):
            self.assertFalse(invoice._igic_repep_sale_taxes())
            self.assertFalse(invoice._igic_export_sale_taxes())

    def test_lease_key_without_lease_position_is_e1(self):
        invoice = self._invoice(self.tax_re_ex)
        self.assertEqual(invoice.verifactu_registration_key_code, "18")
        invoice.verifactu_registration_key = self.key_11
        self.assertTrue(invoice._igic_lease_exemption())
        taxes, _amount_tax, _amount_total = invoice._get_verifactu_taxes_and_total()
        self.assertEqual(taxes["DetalleDesglose"][0]["OperacionExenta"], "E1")

    def test_unknown_exempt_tax_falls_back_to_e6(self):
        invoice = self._invoice(self.tax_igic_r_7)
        self.assertEqual(
            invoice._get_igic_verifactu_exempt_cause(self.tax_igic_r_7, {}),
            "E6",
        )

    def test_non_atc_company_uses_base_breakdown(self):
        spain = self.env.ref("l10n_es_aeat.aeat_tax_agency_spain")
        self.company.tax_agency_id = spain
        invoice = self._invoice(self.tax_igic_r_7, fiscal_position=self.fp_nacional)
        taxes, _amount_tax, _amount_total = invoice._get_verifactu_taxes_and_total()
        self.assertTrue(taxes["DetalleDesglose"])

    def test_tax_not_in_total_and_base_not_in_total(self):
        irpf = self.tax_igic_r_7.copy({"name": "Retención test", "amount": -15})
        self._link_tax_to_map(
            irpf, "TaxNotIncludedInTotal", "account_tax_template_cov_irpf"
        )
        base_tax = self.tax_igic_r_7.copy({"name": "Base fuera de total", "amount": 0})
        self._link_tax_to_map(
            base_tax, "BaseNotIncludedInTotal", "account_tax_template_cov_base"
        )
        invoice = self.env["account.move"].create(
            {
                "company_id": self.company.id,
                "partner_id": self.partner.id,
                "invoice_date": "2026-01-01",
                "move_type": "out_invoice",
                "fiscal_position_id": self.fp_nacional.id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Con retención",
                            "account_id": self.account_expense.id,
                            "price_unit": 100,
                            "quantity": 1,
                            "tax_ids": [Command.set((self.tax_igic_r_7 | irpf).ids)],
                        }
                    ),
                    Command.create(
                        {
                            "name": "Base excluida",
                            "account_id": self.account_expense.id,
                            "price_unit": 40,
                            "quantity": 1,
                            "tax_ids": [Command.set(base_tax.ids)],
                        }
                    ),
                ],
            }
        )
        taxes, amount_tax, amount_total = invoice._get_verifactu_taxes_and_total()
        self.assertEqual(len(taxes["DetalleDesglose"]), 1)
        self.assertEqual(taxes["DetalleDesglose"][0]["CalificacionOperacion"], "S1")
        info = invoice._get_aeat_tax_info()
        irpf_amount = next(
            vals["amount"] for vals in info.values() if vals["tax"] == irpf
        )
        base_amount = next(
            vals["base"] for vals in info.values() if vals["tax"] == base_tax
        )
        self.assertAlmostEqual(
            invoice.amount_total_signed - amount_total, irpf_amount + base_amount
        )
        self.assertAlmostEqual(invoice.amount_tax_signed - amount_tax, irpf_amount)

    def test_unmapped_tax_raises(self):
        tax = self.tax_igic_r_7.copy({"name": "IGIC sin mapa", "amount": 4})
        invoice = self._invoice(tax, fiscal_position=self.fp_nacional)
        with self.assertRaises(UserError):
            invoice._get_verifactu_taxes_and_total()

    def test_default_tax_key_for_atc_company(self):
        key = (
            self.env["account.fiscal.position"]
            .with_company(self.company)
            ._default_verifactu_tax_key()
        )
        self.assertEqual(key, "03")

    def test_create_fiscal_position_without_agency(self):
        original = type(self.env).ref

        def _ref(env, xml_id, raise_if_not_found=True):
            if xml_id == "l10n_es_aeat.aeat_tax_agency_canarias":
                return env["aeat.tax.agency"]
            return original(env, xml_id, raise_if_not_found)

        with patch.object(type(self.env), "ref", _ref):
            fp = self.env["account.fiscal.position"].create(
                {"name": "Sin agencia", "company_id": self.company.id}
            )
        self.assertTrue(fp)


class TestSeparateLeaseAndRecargo(TestVerifactuIgicCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company.write(
            {
                "tax_agency_id": cls.env.ref(
                    "l10n_es_aeat.aeat_tax_agency_canarias"
                ).id,
            }
        )

    def _lease_tax(self, name):
        tax = self.env.ref(
            f"l10n_es_igic.{self.company.id}_account_tax_template_igic_re_ex"
        ).copy({"name": name})
        template = self.env.ref("l10n_es_igic.account_tax_template_igic_re_ex").copy(
            {"name": name}
        )
        self.env["ir.model.data"].create(
            [
                {
                    "name": "account_tax_template_igic_lease_ex",
                    "module": "l10n_es_igic",
                    "model": "account.tax.template",
                    "res_id": template.id,
                },
                {
                    "name": f"{self.company.id}_account_tax_template_igic_lease_ex",
                    "module": "l10n_es_igic",
                    "model": "account.tax",
                    "res_id": tax.id,
                },
            ]
        )
        return tax, template

    def test_separate_lease_and_recargo_migrates_pending_data(self):
        lease_fp = self.env.ref(f"l10n_es_igic.{self.company.id}_fp_lease_canary")
        recargo_fp = self.env.ref(f"l10n_es_igic.{self.company.id}_fp_recargo_canary")
        re_ex = self.env.ref(
            f"l10n_es_igic.{self.company.id}_account_tax_template_igic_re_ex"
        )
        key_18 = self.env.ref(
            "l10n_es_verifactu_oca.verifactu_registration_keys_igic_18"
        )
        lease_tax, lease_template = self._lease_tax("IGIC arrendamiento exento test")
        lease_fp.write(
            {
                "verifactu_tax_key": "01",
                "verifactu_registration_key": key_18.id,
                "tax_ids": [
                    Command.create(
                        {
                            "tax_src_id": self.tax_igic_r_7.id,
                            "tax_dest_id": lease_tax.id,
                        }
                    )
                ],
            }
        )
        recargo_fp.write(
            {
                "verifactu_tax_key": "03",
                "verifactu_registration_key": key_18.id,
            }
        )
        map_line = self.env.ref("l10n_es_verifactu_oca.verifactu_map_line_E1")
        map_line.write({"taxes": [(4, lease_template.id)]})

        self.env["account.fiscal.position"]._igic_verifactu_separate_lease_and_recargo()

        self.assertEqual(lease_fp.verifactu_tax_key, "03")
        self.assertEqual(lease_fp.verifactu_registration_key.code, "11")
        self.assertEqual(lease_fp.tax_ids.tax_dest_id, re_ex)
        self.assertFalse(lease_tax.exists())
        self.assertFalse(lease_template.exists())
        self.assertNotIn(lease_template, map_line.taxes)
        self.assertEqual(recargo_fp.verifactu_registration_key.code, "01")

        lease_tax, lease_template = self._lease_tax("IGIC arrendamiento sin líneas")
        self.env["account.fiscal.position"]._igic_verifactu_separate_lease_and_recargo()
        self.assertFalse(lease_tax.exists())
        self.assertFalse(lease_template.exists())

        spain = self.env.ref("l10n_es_aeat.aeat_tax_agency_spain")
        self.company.tax_agency_id = spain
        self.env["account.fiscal.position"]._igic_verifactu_separate_lease_and_recargo()


class TestExtraVerifactuCompany(TestVerifactuIgicCommon):
    @classmethod
    def _create_extra_verifactu_company(cls):
        cls.extra_company = cls.env["res.company"].create(
            {
                "name": "Otra compañía VERI*FACTU",
                "currency_id": cls.env.ref("base.EUR").id,
                "country_id": cls.env.ref("base.es").id,
                "verifactu_enabled": True,
            }
        )

    def test_other_company_verifactu_is_disabled_during_tests(self):
        self.assertFalse(self.extra_company.verifactu_enabled)
        self.assertIn(self.extra_company.id, self._saved_verifactu_company_states)
