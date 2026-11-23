# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2021 Valentin Vinagre <valentin.vinagre@sygel.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import exceptions, fields
from odoo.orm.model_classes import add_to_registry
from odoo.tests import Form, tagged
from odoo.tools.safe_eval import safe_eval

from odoo.addons.base.tests.common import BaseCommon

TEST_MODEL_NAME = "l10n.es.aeat.mod999.report"


@tagged("post_install", "-at_install")
class TestL10nEsAeatReport(BaseCommon):
    _test_user_groups = (
        "base.group_user",
        "base.group_system",
        "account.group_account_invoice",
        "l10n_es_aeat.group_account_aeat",
    )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Load a test model using odoo.orm.model_classes.add_to_registry
        from .models import L10nEsAeatTestReport

        add_to_registry(cls.env.registry, L10nEsAeatTestReport)
        cls.registry._setup_models__(cls.env.cr, [TEST_MODEL_NAME])
        cls.registry.init_models(
            cls.env.cr, [TEST_MODEL_NAME], {"models_to_check": True}
        )
        cls.env["ir.access"].create(
            {
                "name": "AEAT test report access",
                "model_id": cls.env["ir.model"]._get_id(TEST_MODEL_NAME),
                "group_id": cls.env.ref("base.group_system").id,
                "operation": "crud",
            }
        )
        cls.addClassCleanup(cls.registry.__delitem__, TEST_MODEL_NAME)

        cls.AeatReport = cls.env[TEST_MODEL_NAME]
        cls.period_types = {
            "0A": ("2016-01-01", "2016-12-31"),
            "1T": ("2016-01-01", "2016-03-31"),
            "2T": ("2016-04-01", "2016-06-30"),
            "3T": ("2016-07-01", "2016-09-30"),
            "4T": ("2016-10-01", "2016-12-31"),
            "01": ("2016-01-01", "2016-01-31"),
            "02": ("2016-02-01", "2016-02-29"),
            "03": ("2016-03-01", "2016-03-31"),
            "04": ("2016-04-01", "2016-04-30"),
            "05": ("2016-05-01", "2016-05-31"),
            "06": ("2016-06-01", "2016-06-30"),
            "07": ("2016-07-01", "2016-07-31"),
            "08": ("2016-08-01", "2016-08-31"),
            "09": ("2016-09-01", "2016-09-30"),
            "10": ("2016-10-01", "2016-10-31"),
            "11": ("2016-11-01", "2016-11-30"),
            "12": ("2016-12-01", "2016-12-31"),
        }

    def test_compute_dates(self):
        report = self.AeatReport.new({"year": 2016})
        for period_type in self.period_types:
            report.period_type = period_type
            date_start, date_end = self.period_types[period_type]
            self.assertEqual(
                report.date_start,
                fields.Date.to_date(date_start),
                f"Incorrect start date for period {period_type}: {report.date_start}.",
            )
            self.assertEqual(
                report.date_end,
                fields.Date.to_date(date_end),
                f"Incorrect end date for period {period_type}: {report.date_end}.",
            )
            report.invalidate_recordset(["date_start", "date_end"])

    def test_check_complementary(self):
        report = self.AeatReport.new(
            {
                "year": 2016,
                "statement_type": "S",
            }
        )
        with self.assertRaises(exceptions.UserError):
            report._check_previous_number()

    def test_new_company(self):
        self.assertTrue(TEST_MODEL_NAME in self.env)
        company = self.env["res.company"].create({"name": "Test company"})
        self.assertTrue(
            self.env["ir.sequence"].search(
                [("name", "=", "aeat999-sequence"), ("company_id", "=", company.id)]
            )
        )

    def test_default_representative_vat(self):
        self.env.company.representative_vat = "36477262K"
        report_form = Form(self.AeatReport)
        self.assertEqual(report_form.representative_vat, "36477262K")

    def test_export_to_boe_file(self) -> None:
        export_config = self.env["aeat.model.export.config"].create(
            {
                "name": "Test BOE export config",
                "model_number": "999",
                "model_id": self.env["ir.model"]._get_id(TEST_MODEL_NAME),
                "date_start": "1900-01-01",
                "config_line_ids": [
                    (
                        0,
                        0,
                        {
                            "sequence": 1,
                            "name": "BOE data",
                            "fixed_value": "BOE",
                            "export_type": "string",
                            "size": 3,
                            "alignment": "left",
                        },
                    )
                ],
            }
        )
        report = self.AeatReport.create(
            {
                "company_vat": "12345678Z",
                "contact_name": "Test Contact",
                "contact_phone": "123456789",
                "year": 2026,
                "period_type": "0A",
                "date_start": "2026-01-01",
                "date_end": "2026-12-31",
                "export_config_id": export_config.id,
            }
        )
        wizard = (
            self.env["l10n.es.aeat.report.export_to_boe"]
            .with_context(active_id=report.id, active_model=report._name)
            .create({})
        )

        action = wizard.action_get_file()
        attachment = self.env["ir.attachment"].search(
            [
                ("name", "=", wizard.name),
                ("res_model", "=", report._name),
                ("res_id", "=", report.id),
            ],
            limit=1,
        )

        self.assertEqual(action["res_id"], wizard.id)
        self.assertEqual(wizard.data.content, b"BOE")
        self.assertEqual(attachment.raw.content, b"BOE")

    def test_01_bank_domain_only_accepts_iban_of_report_partner(self):
        report = self.AeatReport.new({"company_id": self.company.id})
        partner = report.partner_id
        bank_model = self.env["res.partner.bank"]
        matching_iban = bank_model.create(
            {
                "partner_id": partner.id,
                "account_number": "ES66 2100 0418 4012 3456 7891",
            }
        )
        other_partner_iban = bank_model.create(
            {
                "partner_id": self.env["res.partner"].create({"name": "Other"}).id,
                "account_number": "ES66 2100 0418 4012 3456 7891",
            }
        )
        non_iban = bank_model.create(
            {"partner_id": partner.id, "account_number": "1234-5678"}
        )
        domain = safe_eval(
            report._fields["partner_bank_id"].domain,
            {"partner_id": partner.id},
        )

        self.assertTrue(bank_model._fields["account_type"].store)
        self.assertEqual(bank_model.search(domain), matching_iban)
        self.assertNotIn(other_partner_iban, bank_model.search(domain))
        self.assertNotIn(non_iban, bank_model.search(domain))
