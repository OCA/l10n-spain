# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.fields import Command
from odoo.orm.model_classes import add_to_registry
from odoo.tests import Form, tagged

from .common import TestL10nEsAeatModBase

TEST_MODEL_NAME = "l10n.es.aeat.mod998.report"


@tagged("post_install", "-at_install")
class TestL10nEsAeatReportTaxMapping(TestL10nEsAeatModBase):
    @classmethod
    def _chart_of_accounts_create(cls):
        # Register the test report before the company is created, so that the
        # company gets its AEAT sequence
        from .models import L10nEsAeatTestTaxMappingReport

        add_to_registry(cls.env.registry, L10nEsAeatTestTaxMappingReport)
        cls.registry._setup_models__(cls.env.cr, [TEST_MODEL_NAME])
        cls.registry.init_models(
            cls.env.cr, [TEST_MODEL_NAME], {"models_to_check": True}
        )
        cls.addClassCleanup(cls.registry.__delitem__, TEST_MODEL_NAME)
        return super()._chart_of_accounts_create()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.access"].create(
            {
                "name": "AEAT test tax mapping report access",
                "model_id": cls.env["ir.model"]._get_id(TEST_MODEL_NAME),
                "group_id": cls.env.ref("l10n_es_aeat.group_account_aeat").id,
                "operation": "crud",
            }
        )
        tax_xmlid = cls.env["l10n.es.aeat.map.tax.line.tax"].create(
            {"name": "account_tax_template_p_iva21_bc"}
        )
        cls.line_vals = line_vals = {
            "move_type": "regular",
            "sum_type": "both",
            "inverse": True,
            "tax_xmlid_ids": [Command.set(tax_xmlid.ids)],
        }
        cls.tax_map = cls.env["l10n.es.aeat.map.tax"].create(
            {
                "model": 998,
                "map_line_ids": [
                    Command.create(
                        dict(line_vals, field_number=1, name="Base", field_type="base")
                    ),
                    Command.create(
                        dict(
                            line_vals, field_number=2, name="Quota", field_type="amount"
                        )
                    ),
                ],
            }
        )

    def _create_bill(self, deductible_percentage):
        bill_form = Form(
            self.env["account.move"]
            .with_user(self.billing_user)
            .with_context(default_move_type="in_invoice")
        )
        bill_form.partner_id = self.supplier
        bill_form.invoice_date = "2024-01-15"
        bill_form.journal_id = self.journal_purchase
        with bill_form.invoice_line_ids.new() as line_form:
            line_form.name = "Mixed use expense"
            line_form.price_unit = 100
            line_form.tax_ids.clear()
            line_form.tax_ids.add(self._get_taxes("P_IVA21_BC"))
            line_form.deductible_percentage = deductible_percentage
        bill = bill_form.save()
        bill.action_post()
        return bill

    def _calculate_report(self):
        report = self.env[TEST_MODEL_NAME].create(
            {
                "name": "9980000000001",
                "company_id": self.company.id,
                "company_vat": "123456789",
                "contact_name": "Test owner",
                "contact_phone": "911234455",
                "year": 2024,
                "period_type": "1T",
                "date_start": "2024-01-01",
                "date_end": "2024-03-31",
            }
        )
        report.button_calculate()
        return {line.field_number: line.amount for line in report.tax_line_ids}

    def test_non_deductible_bill_base(self):
        """A bill line of 100 + 21 % VAT, 50 % deductible: the base is the
        deductible part (50), the base of the deductible quota (10.50), not the
        private part of the tax that Odoo core books on a line with the taxes of
        its account.
        """
        self._create_bill(0.5)
        amounts = self._calculate_report()
        self.assertAlmostEqual(amounts[1], 50.0, 2)
        self.assertAlmostEqual(amounts[2], 10.5, 2)

    def test_non_deductible_bill_both(self):
        """A map line of base and quota adds the deductible base and quota."""
        # The tax maps come from module data, which the user does not edit
        self.tax_map.sudo().map_line_ids = [
            Command.create(
                dict(self.line_vals, field_number=3, name="Both", field_type="both")
            )
        ]
        self._create_bill(0.5)
        amounts = self._calculate_report()
        self.assertAlmostEqual(amounts[3], 60.5, 2)
