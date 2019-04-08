# Copyright 2016-2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.tests import common
from odoo import exceptions

TEST_MODEL_NAME = 'l10n.es.aeat.mod999.report'


class L10nEsAeatTestReport(models.TransientModel):
    _name = TEST_MODEL_NAME
    _inherit = 'l10n.es.aeat.report'
    _aeat_number = '999'


class TestL10nEsAeatReport(common.SavepointCase):
    post_install = True
    at_install = False

    def _init_test_model(cls, model_cls):
        """ It builds a model from model_cls in order to test abstract models.
        Note that this does not actually create a table in the database, so
        there may be some unidentified edge cases.

        Requirements: test to be executed at post_install.

        : Args:
            model_cls (odoo.models.BaseModel): Class of model to initialize
        Returns:
            Instance
        """
        registry = cls.env.registry
        cls.env.cr.execute(
            "INSERT INTO ir_model (model, name) VALUES (%s, %s)",
            (TEST_MODEL_NAME, 'Test AEAT model'),
        )
        inst = model_cls._build_model(registry, cls.env.cr)
        model = cls.env[model_cls._name].with_context(todo=[])
        model._prepare_setup()
        model._setup_base()
        model._setup_fields()
        model._setup_complete()
        model._auto_init()
        model.init()
        return inst

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._init_test_model(cls, L10nEsAeatTestReport)
        cls.AeatReport = cls.env["l10n.es.aeat.report"]
        cls.period_types = {
            '0A': ('2016-01-01', '2016-12-31'),
            '1T': ('2016-01-01', '2016-03-31'),
            '2T': ('2016-04-01', '2016-06-30'),
            '3T': ('2016-07-01', '2016-09-30'),
            '4T': ('2016-10-01', '2016-12-31'),
            '01': ('2016-01-01', '2016-01-31'),
            '02': ('2016-02-01', '2016-02-29'),
            '03': ('2016-03-01', '2016-03-31'),
            '04': ('2016-04-01', '2016-04-30'),
            '05': ('2016-05-01', '2016-05-31'),
            '06': ('2016-06-01', '2016-06-30'),
            '07': ('2016-07-01', '2016-07-31'),
            '08': ('2016-08-01', '2016-08-31'),
            '09': ('2016-09-01', '2016-09-30'),
            '10': ('2016-10-01', '2016-10-31'),
            '11': ('2016-11-01', '2016-11-30'),
            '12': ('2016-12-01', '2016-12-31'),
        }

    def test_onchange_period_type(self):
        with self.env.do_in_onchange():
            report = self.AeatReport.new({
                'year': 2016,
            })
            for period_type in self.period_types:
                report.period_type = period_type
                report.onchange_period_type()
                date_start, date_end = self.period_types[period_type]
                self.assertEqual(
                    report.date_start, date_start,
                    "Incorrect start date for period %s: %s." % (
                        period_type, report.date_start))
                self.assertEqual(
                    report.date_end, date_end,
                    "Incorrect end date for period %s: %s." % (
                        period_type, report.date_end))

    def test_check_complementary(self):
        report = self.AeatReport.new({
            'year': 2016,
            'type': 'S',
        })
        with self.assertRaises(exceptions.UserError):
            report._check_previous_number()

    def test_new_company(self):
        self.assertTrue(TEST_MODEL_NAME in self.env)
        company = self.env['res.company'].create({'name': 'Test company'})
        self.assertTrue(
            self.env['ir.sequence'].search([
                ('name', '=', "aeat999-sequence"),
                ('company_id', '=', company.id),
            ]),
        )
