# Copyright 2026 - OCA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import Command

from odoo.addons.l10n_es_igic_verifactu_oca.hooks import post_init_hook

from .common import TestVerifactuIgicCommon


class TestPostInitHook(TestVerifactuIgicCommon):
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

    def _set_stored_verifactu_keys(self, move, tax_key, registration_key):
        self.env.cr.execute(
            """
            UPDATE account_move
               SET verifactu_tax_key = %s,
                   verifactu_registration_key = %s
             WHERE id = %s
            """,
            (tax_key, registration_key.id, move.id),
        )
        move.invalidate_recordset(["verifactu_tax_key", "verifactu_registration_key"])

    def test_post_init_hook_updates_draft_moves_and_fiscal_positions(self):
        fp = self.fp_nacional.copy({"verifactu_tax_key": "01"})
        draft = self.env["account.move"].create(
            self._create_out_invoice_vals({"fiscal_position_id": False})
        )
        posted = self.env["account.move"].create(
            self._create_out_invoice_vals({"fiscal_position_id": False})
        )
        posted.action_post()
        self._set_stored_verifactu_keys(draft, "01", self.peninsula_reg_key)
        self._set_stored_verifactu_keys(posted, "01", self.peninsula_reg_key)

        post_init_hook(self.env)

        draft.invalidate_recordset(["verifactu_tax_key", "verifactu_registration_key"])
        posted.invalidate_recordset(["verifactu_tax_key", "verifactu_registration_key"])
        fp.invalidate_recordset(["verifactu_tax_key"])

        self.assertEqual(draft.verifactu_tax_key, "03")
        self.assertEqual(draft.verifactu_registration_key, self.igic_reg_key)
        self.assertEqual(fp.verifactu_tax_key, "03")
        self.assertEqual(posted.verifactu_tax_key, "01")
        self.assertEqual(posted.verifactu_registration_key, self.peninsula_reg_key)
