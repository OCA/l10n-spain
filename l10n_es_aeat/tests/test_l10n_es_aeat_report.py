# -*- coding: utf-8 -*-
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.tests import common
from openerp import exceptions


class TestL10nEsAeatReport(common.TransactionCase):
    def setUp(self):
        super(TestL10nEsAeatReport, self).setUp()
        self.AeatReport = self.env["l10n.es.aeat.report"]
        self.period_types = {
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
