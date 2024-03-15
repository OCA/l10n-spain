# Copyright 2022 Sygel - Manuel Regidor
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

from odoo.addons.l10n_es_aeat_mod390.tests.test_l10n_es_aeat_mod390 import (
    TestL10nEsAeatMod390Base,
)


class TestL10nEsAeatMod390OSS(TestL10nEsAeatMod390Base):
    def setUp(self):
        super().setUp()
        self.company.country_id = self.env.ref('base.es')
        self.oss_country = self.env.ref("base.fr")
        general_tax = self.env.ref(
            "l10n_es.%s_account_tax_template_s_iva21b" % self.company.id
        )
        wizard = self.env["l10n.eu.oss.wizard"].create(
            {
                "company_id": self.company.id,
                "general_tax": general_tax.id,
                "todo_country_ids": [(4, self.oss_country.id)],
            }
        )
        wizard.generate_eu_oss_taxes()
        self.taxes_sale = {}
        self.oss_tax = self.env["account.tax"].search(
            [
                ("oss_country_id", "=", self.oss_country.id),
                ("company_id", "=", self.company.id),
            ]
        )
        line_data = {
            "name": "Test for OSS tax",
            "account_id": self.accounts["700000"].id,
            "price_unit": 100,
            "quantity": 1,
            "invoice_line_tax_ids": [(4, self.oss_tax.id)],
        }
        extra_vals = {"invoice_line_ids": [(0, 0, line_data)]}
        self._invoice_sale_create("2021-01-01", extra_vals)
        self._invoice_sale_create("2021-12-31", extra_vals)
        # Create reports
        self.model390_oss = self.model390.copy(
            {
                "company_id": self.company.id,
                "company_vat": "1234567890",
                "year": 2021,
                "name": "OSS4000000390",
                "date_start": "2021-01-01",
                "date_end": "2021-12-31",
            }
        )

    def _check_field_amount(self, report, number, amount):
        lines = report.tax_line_ids.filtered(lambda x: x.field_number == number)
        self.assertAlmostEqual(sum(lines.mapped("amount")), amount)

    def test_l10n_es_aeat_mod390_oss(self):
        self.model390_oss.button_calculate()
        self._check_field_amount(self.model390_oss, 126, 200)
