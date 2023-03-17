# Copyright 2023 Tecnativa - Víctor Martínez
# Copyright 2023 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

from odoo import exceptions

from odoo.addons.l10n_es_aeat_mod303.tests.test_l10n_es_aeat_mod303 import (
    TestL10nEsAeatMod303Base,
)


class TestL10nEsAeatMod303VatProrate(TestL10nEsAeatMod303Base):
    taxes_sale = {
        # tax code: (base, tax_amount)
        "S_IVA21B": (1000, 210),
    }
    taxes_purchase = {
        # tax code: (base, tax_amount)
        "P_IVA21_BC": (500, 105),
    }

    def test_model_303_without_prorate(self):
        self._invoice_sale_create("2017-01-11")
        self._invoice_purchase_create("2017-01-11")
        self.model303.button_calculate()
        self.assertEqual(self.model303.total_devengado, 210)
        self.assertEqual(self.model303.total_deducir, 105)
        self.assertEqual(self.model303.resultado_liquidacion, 105)
        self.assertEqual(self.model303.casilla_44, 0)

    def test_model_303_with_prorate(self):
        # Set vat prorate configuration for company
        self.company.write(
            {
                "with_vat_prorate": True,
                "vat_prorate_ids": [
                    (0, 0, {"date": "2017-01-01", "vat_prorate": 90}),
                ],
            }
        )
        # create invoices + model 303 for 1T
        self._invoice_sale_create("2017-01-01")
        self._invoice_purchase_create("2017-01-01")
        self.model303.button_calculate()
        self.assertEqual(self.model303.total_devengado, 210)
        self.assertEqual(self.model303.total_deducir, 94.5)
        self.assertEqual(self.model303.resultado_liquidacion, 115.5)
        self.assertEqual(self.model303.casilla_44, 0)
        # create invoices + model 303 for 4T
        self._invoice_sale_create("2017-11-01")
        self._invoice_purchase_create("2017-11-01")
        with self.assertRaises(exceptions.ValidationError):
            self.model303_4t.vat_prorate_percent = 101
        self.model303_4t.vat_prorate_percent = 89
        self.model303_4t.button_calculate()
        self.assertEqual(self.model303_4t.prorate_account_id.code[:4], "6341")
        self.assertEqual(self.model303_4t.total_devengado, 210)
        self.assertEqual(self.model303_4t.total_deducir, 93.45)
        self.assertEqual(self.model303_4t.resultado_liquidacion, 116.55)
        self.assertEqual(self.model303_4t.casilla_44, -2.1)
        # Export to BOE and check the inclusion of field 44
        boe_wizard = self.env["l10n.es.aeat.report.export_to_boe"].create(
            {"name": "test_export_to_boe.txt"}
        )
        config = self.env.ref("l10n_es_aeat_mod303.aeat_mod303_2023_main_export_config")
        boe = boe_wizard._export_config(self.model303_4t, config)
        self.assertIn("N0000000000000210", str(boe))
        # Generate regularization move
        self.model303_4t.button_post()
        self.assertTrue(
            self.model303_4t.move_id.line_ids.filtered(lambda x: x.debit == 2.1)
        )
