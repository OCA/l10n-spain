# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2021 Valentin Vinagre <valentin.vinagre@sygel.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo_test_helper import FakeModelLoader

from odoo import exceptions, fields
from odoo.tests import common

TEST_MODEL_NAME = "l10n.es.aeat.mod999.report"


class TestL10nEsAeatReport(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Load a test model using odoo_test_helper
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .models import L10nEsAeatTestReport

        cls.loader.update_registry((L10nEsAeatTestReport,))
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

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        return super().tearDownClass()

    def test_compute_dates(self):
        report = self.AeatReport.new({"year": 2016})
        for period_type in self.period_types:
            report.period_type = period_type
            date_start, date_end = self.period_types[period_type]
            self.assertEqual(
                report.date_start,
                fields.Date.to_date(date_start),
                "Incorrect start date for period %s: %s."
                % (period_type, report.date_start),
            )
            self.assertEqual(
                report.date_end,
                fields.Date.to_date(date_end),
                "Incorrect end date for period %s: %s."
                % (period_type, report.date_end),
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
