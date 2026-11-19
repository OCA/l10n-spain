# Copyright 2026 - OCA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import Command

from ..hooks import post_init_hook, pre_init_hook
from .common import TestVerifactuIgicCommon


class TestVerifactuTaxKey(TestVerifactuIgicCommon):
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
        cls.igic_reg_key = cls.env.ref(
            "l10n_es_verifactu_oca.verifactu_registration_keys_igic_01"
        )
        cls.peninsula_reg_key = cls.env.ref(
            "l10n_es_verifactu_oca.verifactu_registration_keys_01"
        )

    def _create_out_invoice_vals(self, extra_vals=None):
        vals = {
            "company_id": self.company.id,
            "partner_id": self.partner.id,
            "invoice_date": "2026-01-01",
            "move_type": "out_invoice",
            "invoice_line_ids": [
                Command.create(
                    {
                        "product_id": self.product.id,
                        "account_id": self.account_expense.id,
                        "name": "Test line",
                        "price_unit": 100,
                        "quantity": 1,
                    }
                )
            ],
        }
        if extra_vals:
            vals.update(extra_vals)
        return vals

    def test_atc_invoice_without_fp_uses_igic_tax_key(self):
        invoice = self.env["account.move"].create(
            self._create_out_invoice_vals({"fiscal_position_id": False})
        )
        self.assertEqual(invoice.verifactu_tax_key, "03")
        self.assertEqual(invoice.verifactu_registration_key, self.igic_reg_key)

    def test_atc_invoice_keys_ignore_current_company(self):
        mainland = self.env["res.company"].create({"name": "Mainland company"})
        mainland.tax_agency_id = self.env.ref("l10n_es_aeat.aeat_tax_agency_spain")
        self.env.user.write({"company_ids": [(4, mainland.id)]})
        env = self.env(
            context=dict(
                self.env.context,
                allowed_company_ids=[mainland.id, self.company.id],
            )
        )
        invoice = env["account.move"].create(
            self._create_out_invoice_vals({"fiscal_position_id": False})
        )
        self.assertEqual(env.company, mainland)
        self.assertEqual(invoice.verifactu_tax_key, "03")
        self.assertEqual(invoice.verifactu_registration_key, self.igic_reg_key)

    def test_atc_invoice_keys_recompute_when_agency_changes(self):
        invoice = self.env["account.move"].create(
            self._create_out_invoice_vals({"fiscal_position_id": False})
        )
        original_agency = self.company.tax_agency_id
        try:
            self.company.tax_agency_id = self.env.ref(
                "l10n_es_aeat.aeat_tax_agency_spain"
            )
            self.assertEqual(invoice.verifactu_tax_key, "01")
            self.assertEqual(invoice.verifactu_registration_key, self.peninsula_reg_key)
        finally:
            self.company.tax_agency_id = original_agency

    def test_atc_invoice_keys_recompute_when_fp_keys_change(self):
        fp = self.fp_nacional.copy(
            {
                "verifactu_tax_key": "03",
                "verifactu_registration_key": self.igic_reg_key.id,
            }
        )
        invoice = self.env["account.move"].create(
            self._create_out_invoice_vals({"fiscal_position_id": fp.id})
        )
        fp.verifactu_registration_key = self.fp_registration_key_17
        self.assertEqual(
            invoice.verifactu_registration_key, self.fp_registration_key_17
        )
        fp.verifactu_tax_key = "05"
        self.assertEqual(invoice.verifactu_tax_key, "05")

    def test_backfill_canary_fiscal_positions_and_drafts(self):
        self.fp_nacional.write(
            {"verifactu_tax_key": "01", "verifactu_registration_key": False}
        )
        invoice = self.env["account.move"].create(
            self._create_out_invoice_vals({"fiscal_position_id": self.fp_nacional.id})
        )
        invoice.write(
            {
                "verifactu_tax_key": "01",
                "verifactu_registration_key": self.peninsula_reg_key.id,
            }
        )
        invoice_without_fp = self.env["account.move"].create(
            self._create_out_invoice_vals({"fiscal_position_id": False})
        )
        invoice_without_fp.write(
            {
                "verifactu_tax_key": "01",
                "verifactu_registration_key": self.peninsula_reg_key.id,
            }
        )

        pre_init_hook(self.env)

        self.assertEqual(self.fp_nacional.verifactu_tax_key, "03")
        self.assertEqual(self.fp_nacional.verifactu_registration_key, self.igic_reg_key)
        for document in invoice | invoice_without_fp:
            self.assertEqual(document.verifactu_tax_key, "03")
            self.assertEqual(document.verifactu_registration_key, self.igic_reg_key)

    def test_post_init_backfills_drafts_without_touching_posted(self):
        draft = self.env["account.move"].create(
            self._create_out_invoice_vals({"fiscal_position_id": self.fp_nacional.id})
        )
        draft.write({"verifactu_tax_key": "01", "verifactu_registration_key": False})
        posted = self.env["account.move"].create(
            self._create_out_invoice_vals({"fiscal_position_id": False})
        )
        posted.action_post()
        posted.write({"verifactu_tax_key": False, "verifactu_registration_key": False})

        post_init_hook(self.env)

        self.assertEqual(draft.verifactu_tax_key, "03")
        self.assertEqual(draft.verifactu_registration_key, self.igic_reg_key)
        self.assertFalse(posted.verifactu_tax_key)
        self.assertFalse(posted.verifactu_registration_key)

    def test_atc_invoice_with_fp_without_tax_key_uses_igic(self):
        fp = self.fp_nacional.copy({"verifactu_tax_key": False})
        invoice = self.env["account.move"].create(
            self._create_out_invoice_vals({"fiscal_position_id": fp.id})
        )
        self.assertEqual(invoice.verifactu_tax_key, "03")

    def test_atc_import_surcharge_fp_uses_neutral_igic_key(self):
        self.assertEqual(self.fp_recargo.verifactu_tax_key, "03")
        self.assertEqual(self.fp_recargo.verifactu_registration_key, self.igic_reg_key)
        invoice = self.env["account.move"].create(
            self._create_out_invoice_vals({"fiscal_position_id": self.fp_recargo.id})
        )
        self.assertEqual(invoice.verifactu_tax_key, "03")
        self.assertEqual(invoice.verifactu_registration_key, self.igic_reg_key)
        self.assertEqual(invoice.verifactu_registration_key_code, "01")

    def test_atc_fiscal_position_default_tax_key_on_create(self):
        fp = self.env["account.fiscal.position"].create(
            {
                "name": "ATC test FP",
                "company_id": self.company.id,
            }
        )
        self.assertEqual(fp.verifactu_tax_key, "03")

    def test_fiscal_position_default_uses_target_company(self):
        mainland = self.env["res.company"].create({"name": "Mainland company"})
        mainland.tax_agency_id = self.env.ref("l10n_es_aeat.aeat_tax_agency_spain")
        fp = self.env["account.fiscal.position"].create(
            {"name": "Mainland FP", "company_id": mainland.id}
        )
        defaults = (
            self.env["account.fiscal.position"]
            .with_context(default_company_id=mainland.id)
            .default_get(["verifactu_tax_key"])
        )
        self.assertEqual(fp.verifactu_tax_key, "01")
        self.assertEqual(defaults["verifactu_tax_key"], "01")

    def test_igic_exempt_reasons_are_not_available_for_peninsula(self):
        mainland = self.env["res.company"].create({"name": "Mainland company"})
        mainland.tax_agency_id = self.env.ref("l10n_es_aeat.aeat_tax_agency_spain")
        self.env.user.write({"company_ids": [(4, mainland.id)]})
        canary_reasons = dict(
            self.env["account.tax"]
            ._fields["l10n_es_exempt_reason"]
            ._description_selection(self.env)
        )
        mainland_env = self.env(
            context=dict(
                self.env.context,
                allowed_company_ids=[mainland.id, self.company.id],
            )
        )
        mainland_reasons = dict(
            mainland_env["account.tax"]
            ._fields["l10n_es_exempt_reason"]
            ._description_selection(mainland_env)
        )
        self.assertIn("E7", canary_reasons)
        self.assertIn("E8", canary_reasons)
        self.assertNotIn("E7", mainland_reasons)
        self.assertNotIn("E8", mainland_reasons)

    def test_peninsula_company_keeps_iva_tax_key(self):
        spain_agency = self.env.ref("l10n_es_aeat.aeat_tax_agency_spain")
        original_agency = self.company.tax_agency_id
        self.company.tax_agency_id = spain_agency
        try:
            invoice = self.env["account.move"].create(
                self._create_out_invoice_vals({"fiscal_position_id": False})
            )
            self.assertEqual(invoice.verifactu_tax_key, "01")
            self.assertEqual(invoice.verifactu_registration_key, self.peninsula_reg_key)
        finally:
            self.company.tax_agency_id = original_agency
