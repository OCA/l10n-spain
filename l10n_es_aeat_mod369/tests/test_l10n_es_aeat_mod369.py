# Copyright 2022 Planeta Huerto - Juanjo Algaz <jalgaz@gmail.com>
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

import logging

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import \
    TestL10nEsAeatModBase
from odoo.tests.common import Form

_logger = logging.getLogger('aeat.369')


class TestL10nEsAeatMod369Base(TestL10nEsAeatModBase):

    def setUp(self):
        super().setUp()

        self.price_unit = 100
        self.quantity = 5
        general_tax = self.env.ref(
            "l10n_es.%s_account_tax_template_s_iva21b" % self.company.id
        )
        oss_country = self.env.ref("base.fr")
        wizard = self.env["l10n.eu.oss.wizard"].create(
            {
                "company_id": self.company.id,
                "general_tax": general_tax.id,
                "todo_country_ids": [(4, oss_country.id)],
            }
        )
        wizard.generate_eu_oss_taxes()
        self.oss_tax = self.env["account.tax"].search(
            [
                ("oss_country_id", "=", oss_country.id),
                ("company_id", "=", self.company.id),
            ]
        )

        fpo = self.env['account.fiscal.position'].search(
            [('name', '=', 'Intra-EU B2C in France (EU-OSS-FR)')])
        fpo.write({
            'oss_regimen': 'union',
            'outside_spain': True
        })
        line_data = {
            "name": "Test for OSS tax",
            "account_id": self.accounts["700000"].id,
            "price_unit": self.price_unit,
            "quantity": self.quantity,
            "invoice_line_tax_ids": [(4, self.oss_tax.id)],
        }
        extra_vals = {
            "fiscal_position_id": fpo.id,
            "invoice_line_ids": [(0, 0, line_data)]
        }
        self.inv1 = self._invoice_sale_create("2022-11-01", extra_vals)
        self.inv2 = self._invoice_sale_create("2023-01-01", extra_vals)

        # Create reports
        mod369_form = Form(self.env["l10n.es.aeat.mod369.report"])
        mod369_form.company_id = self.company
        mod369_form.company_vat = "1234567890"
        self.model369 = mod369_form.save()
        self.model369_2022_4t = self.model369.copy(
            {
                "name": "3690000000002",
                "period_type": "4T",
                "date_start": "2022-10-01",
                "date_end": "2022-12-31",
                "year": 2022
            }
        )

    def test_model_369(self):
        self.model369_2022_4t.button_calculate()
        amount_tax = self.inv1.amount_tax
        self.assertTrue(amount_tax)
        self.assertEqual(amount_tax, self.model369_2022_4t.total_amount)
        num_invoices = len(
            self.model369_2022_4t.tax_line_ids.mapped('move_line_ids').mapped(
                'invoice_id'))
        self.assertEqual(1, num_invoices)
        pages_5_6_total = sum(
            self.model369_2022_4t.total_line_ids.mapped('page_5_6_total'))
        self.assertEqual(amount_tax, pages_5_6_total)
