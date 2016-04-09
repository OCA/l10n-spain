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
