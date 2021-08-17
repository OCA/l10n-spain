# -*- coding: utf-8 -*-
# © 2016 Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

from openerp.tests import common


class TestL10nEsAeatMod303Base(object):
    def setUp(self):
        super(TestL10nEsAeatMod303Base, self).setUp()
        self.partner = self.env['res.partner'].create({'name': 'Test partner'})
        self.product = self.env['product.product'].create({
            'name': 'Test product',
        })
        self.account_type = self.env['account.account.type'].create({
            'name': 'Test account type',
            'code': 'TEST',
        })
        self.account_expense = self.env['account.account'].create({
            'name': 'Test expense account',
            'code': 'EXP',
            'type': 'other',
            'user_type': self.account_type.id,
        })
        self.analytic_account_1 = self.env['account.analytic.account'].create({
            'name': 'Test analytic account 1',
            'type': 'normal',
        })
        self.analytic_account_2 = self.env['account.analytic.account'].create({
            'name': 'Test analytic account 2',
            'type': 'normal',
        })
        self.account_tax = self.env['account.account'].create({
            'name': 'Test tax account',
            'code': 'TAX',
            'type': 'other',
            'user_type': self.account_type.id,
        })
        self.base_code = self.env['account.tax.code'].create({
            'name': '[28] Test base code',
            'code': 'OICBI',
        })
        self.tax_code = self.env['account.tax.code'].create({
            'name': '[29] Test tax code',
            'code': 'SOICC',
        })
        self.tax = self.env['account.tax'].create({
            'name': 'Test tax 10%',
            'type_tax_use': 'purchase',
            'type': 'percent',
            'amount': '0.10',
            'account_collected_id': self.account_tax.id,
            'base_code_id': self.base_code.id,
            'base_sign': 1,
            'tax_code_id': self.tax_code.id,
            'tax_sign': 1,
        })
        self.period = self.env['account.period'].find()
        self.invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'type': 'in_invoice',
            'period_id': self.period.id,
            'account_id': self.partner.property_account_payable.id,
            'invoice_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'account_id': self.account_expense.id,
                    'account_analytic_id': self.analytic_account_1.id,
                    'name': 'Test line',
                    'price_unit': 100,
                    'quantity': 1,
                    'invoice_line_tax_id': [(6, 0, self.tax.ids)],
                }),
                (0, 0, {
                    'product_id': self.product.id,
                    'account_id': self.account_expense.id,
                    'account_analytic_id': self.analytic_account_2.id,
                    'name': 'Test line',
                    'price_unit': 100,
                    'quantity': 2,
                    'invoice_line_tax_id': [(6, 0, self.tax.ids)],
                }),
                (0, 0, {
                    'product_id': self.product.id,
                    'account_id': self.account_expense.id,
                    'name': 'Test line',
                    'price_unit': 100,
                    'quantity': 1,
                    'invoice_line_tax_id': [(6, 0, self.tax.ids)],
                }),
            ],
        })
        self.invoice.signal_workflow('invoice_open')
        self.model303 = self.env['l10n.es.aeat.mod303.report'].create({
            'company_vat': '1234567890',
            'contact_phone': 'X',
            'fiscalyear_id': self.period.fiscalyear_id.id,
            'periods': [(6, 0, self.period.ids)],
        })


class TestL10nEsAeatMod303(TestL10nEsAeatMod303Base, common.TransactionCase):
    def test_model_303(self):
        self.model303.button_calculate()
        self.assertEqual(self.model303.total_deducir, 40)
        self.assertEqual(self.model303.casilla_46, -40)
        self.assertEqual(self.model303.casilla_69, -40)
        # Export to BOE
        export_to_boe = self.env['l10n.es.aeat.report.export_to_boe'].create({
            'name': 'test_export_to_boe.txt',
        })
        export_config_xml_ids = [
            'l10n_es_aeat_mod303.aeat_mod303_2018_main_export_config',
            'l10n_es_aeat_mod303.aeat_mod303_2021_main_export_config',
            'l10n_es_aeat_mod303.aeat_mod303_202107_main_export_config',
        ]
        for xml_id in export_config_xml_ids:
            export_config = self.env.ref(xml_id)
            self.assertTrue(
                export_to_boe._export_config(self.model303, export_config)
            )
        with self.assertRaises(exceptions.ValidationError):
            self.model303.cuota_compensar = -250
        self.model303.button_post()
        self.assertTrue(self.model303.move_id)
        self.assertEqual(self.model303.move_id.ref, self.model303.name)
        self.assertEqual(
            self.model303.move_id.journal_id, self.model303.journal_id,
        )
        self.assertEqual(self.model303.move_id.partner_id,
                         self.env.ref('l10n_es_aeat.res_partner_aeat'))
        codes = self.model303.move_id.mapped('line_ids.account_id.code')
        self.assertIn('475000', codes)
        self.assertIn('477000', codes)
        self.assertIn('472000', codes)
        self.model303.button_unpost()
        self.assertFalse(self.model303.move_id)
        self.assertEqual(self.model303.state, 'cancelled')
        self.model303.button_recover()
        self.assertEqual(self.model303.state, 'draft')
        self.assertEqual(self.model303.calculation_date, False)
        self.model303.button_cancel()
        self.assertEqual(self.model303.state, 'cancelled')
        # Check 4T without exonerated
        self.model303_4t.button_calculate()
        self.assertAlmostEqual(
            self.model303_4t.tax_line_ids.filtered(
                lambda x: x.field_number == 80
            ).amount, 0,
        )
        # Check 4T with exonerated
        self.model303_4t.exonerated_390 = '1'
        self.model303_4t.button_calculate()
        self.assertAlmostEqual(
            self.model303_4t.tax_line_ids.filtered(
                lambda x: x.field_number == 80
            ).amount, 14280.0,
        )
        self.assertAlmostEqual(
            self.model303_4t.casilla_88, 35680.0,
        )
        # Check change of period type
        self.model303_4t.period_type = '1T'
        self.model303_4t.onchange_period_type()
        self.assertEqual(self.model303_4t.exonerated_390, '2')

    def test_model_303_negative_special_case(self):
        self.taxes_sale = {
            # tax code: (base, tax_amount)
            'S_IVA4B': (1000, 40),
            'S_IVA21B//neg': (-140, -29.4),
        }
        self.taxes_purchase = {
            # tax code: (base, tax_amount)
            'P_IVA4_BC': (240, 9.6),
            'P_IVA21_SC//neg': (-23, -4.83),
        }
        self.taxes_result = {
            # Régimen General - Base imponible 4%
            '1': 1000,  # S_IVA4B
            # Régimen General - Cuota 4%
            '3': 40,  # S_IVA4B
            # Régimen General - Base imponible 21%
            '7': -140,  # S_IVA21B
            # Régimen General - Cuota 21%
            '9': -29.4,  # S_IVA21B
            # Modificación bases y cuotas - Base (Compras y ventas)
            '14': 0,
            # Modificación bases y cuotas - Cuota (Compras y ventas)
            '15': 0,
            # Cuotas soportadas en op. int. corrientes - Base
            '28': 240 - 23,  # P_IVA4_IC_BC, P_IVA21_SC
            # Cuotas soportadas en op. int. corrientes - Cuota
            '29': 9.6 - 4.83,  # P_IVA4_IC_BC, P_IVA21_SC
        }
        self._invoice_sale_create('2020-01-01')
        self._invoice_purchase_create('2020-01-01')
        self.model303.date_start = '2020-01-01'
        self.model303.date_end = '2020-03-31'
        self.model303.button_calculate()
        self._check_tax_lines()
