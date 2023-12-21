# Copyright 2021 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

from odoo.tests.common import Form

from odoo.addons.l10n_es_aeat_mod303.tests.test_l10n_es_aeat_mod303 import (
    TestL10nEsAeatMod303Base,
)


class TestL10nEsAeatMod303(TestL10nEsAeatMod303Base):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                mail_create_nolog=True,
                mail_create_nosubscribe=True,
                mail_notrack=True,
                no_reset_password=True,
                tracking_disable=True,
            )
        )
        cls.oss_country = cls.env.ref("base.fr")
        cls.company.country_id = cls.env.ref("base.es").id
        cls.company.account_fiscal_country_id = cls.env.ref("base.es").id
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
        cls.fr_fiscal_position = cls.env["account.fiscal.position"].search(
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
            "fiscal_position_id": cls.fr_fiscal_position.id,
        }
        cls.invoice_1 = cls._invoice_sale_create("2021-07-01", extra_vals)
        cls.invoice_2 = cls._invoice_sale_create("2021-11-01", extra_vals)
        # Create reports
        mod303_form = Form(cls.env["l10n.es.aeat.mod303.report"])
        mod303_form.company_id = cls.company
        mod303_form.year = 2021
        mod303_form.period_type = "3T"
        mod303_form.company_vat = "1234567890"
        cls.model303 = mod303_form.save()
        cls.model303_4t = cls.model303.copy(
            {
                "name": "OSS4000000303",
                "exonerated_390": "1",
                "has_operation_volume": True,
                "period_type": "4T",
                "date_start": "2021-10-01",
                "date_end": "2021-12-31",
            }
        )

    def _check_field_amount(self, report, number, amount):
        lines = report.tax_line_ids.filtered(lambda x: x.field_number == number)
        self.assertAlmostEqual(sum(lines.mapped("amount")), amount)

    def test_l10n_es_aeat_mod303_oss(self):
        self.assertEqual(self.invoice_1.fiscal_position_id, self.fr_fiscal_position)
        self.assertEqual(self.invoice_2.fiscal_position_id, self.fr_fiscal_position)
        self.model303.button_calculate()
        self._check_field_amount(self.model303, 123, 100)
        self._check_field_amount(self.model303, 126, 0)
        self.model303_4t.button_calculate()
        self._check_field_amount(self.model303_4t, 123, 100)
        self._check_field_amount(self.model303_4t, 126, 200)
