##############################################################################
#
# Copyright (c) 2023 Binhex System Solutions
# Copyright (c) 2023 Nicolás Ramos (http://binhex.es)
#
# The licence is in the file __manifest__.py
##############################################################################

from odoo import exceptions

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)



# Tests creating a new instance of the class with valid parameters.
def test_create_instance(self):
    report = self.env['l10n.es.atc.mod415.report'].create({
        'name': 'Test Report',
        'date_start': '2022-01-01',
        'date_end': '2022-03-31',
    })
    self.assertEqual(report.name, 'Test Report')
    self.assertEqual(report.date_start, '2022-01-01')
    self.assertEqual(report.date_end, '2022-03-31')

# Tests calling the calculate method and verifying the expected results.
def test_calculate(self):
    report = self.env['l10n.es.atc.mod415.report'].create({
        'name': 'Test Report',
        'date_start': '2022-01-01',
        'date_end': '2022-03-31',
    })
    partner_record = self.env['l10n.es.atc.mod415.partner_record'].create({
        'report_id': report.id,
        'partner_id': self.env.ref('base.res_partner_2').id,
        'operation_key': 'A',
        'amount': 1000.0,
    })
    report.calculate()
    self.assertEqual(report.total_partner_records, 1)
    self.assertEqual(report.total_amount, 1000.0)
    self.assertEqual(report.total_cash_amount, 0.0)
    self.assertEqual(report.total_real_estate_transmissions_amount, 0.0)
    self.assertEqual(report.total_real_estate_records, 0)
    self.assertEqual(report.total_real_estate_amount, 0.0)

# Tests with a large number of partner records and real estate records.
def test_large_records(self):
    report = self.env['l10n.es.atc.mod415.report'].create({
        'name': 'Test Report',
        'date_start': '2022-01-01',
        'date_end': '2022-03-31',
    })
    partner_ids = []
    for i in range(100):
        partner = self.env['res.partner'].create({
            'name': f'Test Partner {i}',
            'vat': f'ES12345678{i}',
        })
        partner_ids.append(partner.id)
    self.env['account.move.line'].create({
        'partner_id': partner_ids[0],
        'debit': 1000.0,
        'credit': 0.0,
        'date': '2022-01-01',
    })
    self.env['account.move.line'].create({
        'partner_id': partner_ids[1],
        'debit': 2000.0,
        'credit': 0.0,
        'date': '2022-01-01',
    })
    self.env['account.move.line'].create({
        'partner_id': partner_ids[2],
        'debit': 3000.0,
        'credit': 0.0,
        'date': '2022-01-01',
    })
    self.env['account.move.line'].create({
        'partner_id': partner_ids[3],
        'debit': 4000.0,
        'credit': 0.0,
        'date': '2022-01-01',
    })
    report.calculate()
    self.assertEqual(report.total_partner_records, 4)
    self.assertEqual(report.total_amount, 10000.0)

# Tests with extreme values for operations_limit and received_cash_limit.
def test_extreme_values(self):
    report = self.env['l10n.es.atc.mod415.report'].create({
        'name': 'Test Report',
        'date_start': '2022-01-01',
        'date_end': '2022-03-31',
        'operations_limit': 1000000000.0,
        'received_cash_limit': 1000000000.0,
    })
    report.calculate()
    self.assertEqual(report.total_partner_records, 0)
    self.assertEqual(report.total_amount, 0.0)
    self.assertEqual(report.total_cash_amount, 0.0)
    self.assertEqual(report.total_real_estate_transmissions_amount, 0.0)
    self.assertEqual(report.total_real_estate_records, 0)
    self.assertEqual(report.total_real_estate_amount, 0.0)

# Tests that the button_confirm method raises an exception if there are errors in the partner or real estate records.
def test_error_handling(self):
    report = self.env['l10n.es.atc.mod415.report'].create({
        'name': 'Test Report',
        'date_start': '2022-01-01',
        'date_end': '2022-03-31',
    })
    partner_record = self.env['l10n.es.atc.mod415.partner_record'].create({
        'report_id': report.id,
        'partner_id': self.env.ref('base.res_partner_2').id,
        'operation_key': 'A',
        'amount': 1000.0,
        'check_ok': False,
    })
    with self.assertRaises(exceptions.ValidationError):
        report.button_confirm()

# Tests with different combinations of period_yearly, period_quarterly, and period_monthly.
def test_period_combinations(self):
    report = self.env['l10n.es.atc.mod415.report'].create({
        'name': 'Test Report',
        'date_start': '2022-01-01',
        'date_end': '2022-03-31',
        'period_yearly': True,
        'period_quarterly': False,
        'period_monthly': False,
    })
    self.assertTrue(report.period_yearly)
    self.assertFalse(report.period_quarterly)
    self.assertFalse(report.period_monthly)