# Copyright 2023 Tecnativa - Víctor Martínez
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

from odoo.addons.l10n_es_aeat_mod303.tests.test_l10n_es_aeat_mod303 import (
    TestL10nEsAeatMod303Base,
)


class TestL10nEsAeatMod303VatProrate(TestL10nEsAeatMod303Base):
    taxes_sale = {
        # tax code: (base, tax_amount)
        "S_IVA21B": (1000, 0),
    }

    def test_model_303_without_prorate(self):
        self._invoice_sale_create("2017-01-11")
        self.model303.button_calculate()
        self.assertEqual(self.model303.total_devengado, 210)
        self.assertEqual(self.model303.total_deducir, 0)
        self.assertEqual(self.model303.resultado_liquidacion, 210)

    def test_model_303_with_prorate(self):
        # Set vat prorate configuration from company and taxes
        self.company.write(
            {
                "with_vat_prorate": True,
                "vat_prorate_ids": [
                    (0, 0, {"date": "2017-01-01", "vat_prorate": 99}),
                ],
            }
        )
        for desc, _values in self.taxes_sale.items():
            taxes = self._get_taxes(desc.split("//")[0])
            taxes.with_vat_prorate = True
        # Create invoice + calculate 303
        self._invoice_sale_create("2017-01-11")
        self.model303.button_calculate()
        self.assertEqual(self.model303.total_devengado, 210)
        self.assertEqual(self.model303.total_deducir, 207.9)
        self.assertEqual(self.model303.resultado_liquidacion, 2.1)
