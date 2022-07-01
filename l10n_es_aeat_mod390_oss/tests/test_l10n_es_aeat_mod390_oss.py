# Copyright 2022 Sygel - Manuel Regidor
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

from odoo.tests.common import Form

from odoo.addons.l10n_es_aeat_mod390.tests.test_l10n_es_aeat_mod390 import (
    TestL10nEsAeatMod390Base,
)


class TestL10nEsAeatMod390OSS(TestL10nEsAeatMod390Base):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.oss_country = cls.env.ref("base.fr")
        general_tax = cls.env.ref(
            "l10n_es.%s_account_tax_template_s_iva21b" % cls.company.id
        )
        wizard = cls.env["l10n.eu.oss.wizard"].create(
            {
                "company_id": cls.company.id,
                "general_tax": general_tax.id,
                "todo_country_ids": [(4, cls.oss_country.id)],
            }
        )
        wizard.generate_eu_oss_taxes()
        fr_fiscal_position = cls.env["account.fiscal.position"].search(
            [("country_id", "=", cls.oss_country.id), ("oss_oca", "=", True)], limit=1
        )
        cls.taxes_sale = {}
        cls.oss_tax = cls.env["account.tax"].search(
            [
                ("oss_country_id", "=", cls.oss_country.id),
                ("company_id", "=", cls.company.id),
            ]
        )
        line_data = {
            "name": "Test for OSS tax",
            "account_id": cls.accounts["700000"].id,
            "price_unit": 100,
            "quantity": 1,
            "tax_ids": [(4, cls.oss_tax.id)],
        }
        extra_vals = {
            "invoice_line_ids": [(0, 0, line_data)],
            "fiscal_position_id": fr_fiscal_position.id,
        }
        cls._invoice_sale_create("2021-01-01", extra_vals)
        cls._invoice_sale_create("2021-12-31", extra_vals)
        # Create reports
        mod390_form = Form(cls.env["l10n.es.aeat.mod390.report"])
        mod390_form.company_id = cls.company
        mod390_form.year = 2021
        mod390_form.company_vat = "1234567890"
        cls.model390 = mod390_form.save()
        cls.model390 = cls.model390.copy(
            {
                "name": "OSS4000000390",
                "date_start": "2021-01-01",
                "date_end": "2021-12-31",
            }
        )

    def _check_field_amount(self, report, number, amount):
        lines = report.tax_line_ids.filtered(lambda x: x.field_number == number)
        self.assertAlmostEqual(sum(lines.mapped("amount")), amount)

    def test_l10n_es_aeat_mod390_oss(self):
        self.model390.button_calculate()
        self._check_field_amount(self.model390, 126, 200)
