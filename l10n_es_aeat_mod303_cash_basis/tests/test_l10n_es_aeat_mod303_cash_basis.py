# -*- coding: utf-8 -*-
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

from odoo.addons.l10n_es_aeat_mod303.tests.test_l10n_es_aeat_mod303 \
    import TestL10nEsAeatMod303Base


class TestL10nEsAeatMod303CashBasis(TestL10nEsAeatMod303Base):
    def setUp(self):
        super(TestL10nEsAeatMod303CashBasis, self).setUp()
        self.account_type = self.env['account.account.type'].create({
            'name': 'Test account type',
            'type': 'other',
        })
        self.account = self.env['account.account'].create({
            'name': 'Test cash basis account',
            'code': 'CASH_BASIS',
            'user_type_id': self.account_type.id,
        })
        self.journal = self.env['account.journal'].create({
            'name': 'Test cash basis journal',
            'code': 'TCBJ',
            'type': 'general',
            'default_credit_account_id': self.account.id,
            'default_debit_account_id': self.account.id,
        })
        self.env.user.company_id.tax_cash_basis_journal_id = self.journal.id
        taxes = self.env['account.tax'].search([
            ('description', 'in', ('S_IVA21B', 'P_IVA21_BC')),
            ('company_id', '=', self.env.user.company_id.id),
        ])
        taxes.write({
            'use_cash_basis': True,
            'cash_basis_account': self.account.id,
        })
        self.taxes_sale = {
            # tax code: (base, tax_amount)
            'S_IVA21B': (1000, 210),
        }
        self.taxes_purchase = {
            # tax code: (base, tax_amount)
            'P_IVA21_BC': (2000, 420),
        }
        self.sale_invoice = self._invoice_purchase_create('2017-01-03')
        self.purchase_invoice = self._invoice_sale_create('2017-01-13')
        self.model303_2t = self.model303.copy({
            'name': '9994000000303',
            'period_type': '2T',
            'date_start': '2017-04-01',
            'date_end': '2017-06-30',
        })

    def _register_payment(self, invoice, date):
        wizard = self.env['account.register.payments'].with_context(
            active_model='account.invoice',
            active_ids=invoice.ids,
        ).create({
            'journal_id': self.journal.id,
            'payment_method_id': (
                self.env.ref('account.account_payment_method_manual_in').id
            ),
            'payment_date': date,
            'communication': 'Test payment',
        })
        wizard.create_payment()

    def _check_results(self, model, tax_results):
        for field, expected_result in tax_results.items():
            lines = model.tax_line_ids.filtered(
                lambda x: x.field_number == int(field)
            )
            self.assertAlmostEqual(
                expected_result, sum(lines.mapped('amount')), 2,
                "Incorrect result in field %s" % field,
            )

    def test_mod303_cash_basis(self):
        self._register_payment(self.sale_invoice, '2017-04-01')
        self._register_payment(self.purchase_invoice, '2017-04-01')
        # Defaults
        self.assertTrue(self.model303._default_cash_basis_receivable())
        self.assertTrue(self.model303._default_cash_basis_payable())
        # First trimester
        self.model303.button_calculate()
        tax_results = {
            '7': 0,
            '9': 0,
            '28': 0,
            '29': 0,
            '62': 1000,
            '63': 210,
            '74': 2000,
            '75': 420,
        }
        self._check_results(self.model303, tax_results)
        # Second trimester
        self.model303_2t.button_calculate()
        tax_results = {
            '7': 1000,
            '9': 210,
            '28': 2000,
            '29': 420,
            '62': 0,
            '63': 0,
            '74': 0,
            '75': 0,
        }
        self._check_results(self.model303_2t, tax_results)

    def test_mod303_cash_basis_same_period(self):
        self._register_payment(self.sale_invoice, '2017-03-30')
        self._register_payment(self.purchase_invoice, '2017-03-30')
        self.model303.button_calculate()
        tax_results = {
            '7': 1000,
            '9': 210,
            '28': 2000,
            '29': 420,
            '62': 0,
            '63': 0,
            '74': 0,
            '75': 0,
        }
        self._check_results(self.model303, tax_results)
