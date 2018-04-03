# -*- coding: utf-8 -*-
# © 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

import logging
from openerp.tests import common

_logger = logging.getLogger('aeat')


@common.at_install(False)
@common.post_install(True)
class TestL10nEsAeatModBase(common.TransactionCase):
    accounts = {}
    # Set 'debug' attribute to True to easy debug this test
    # Do not forget to include '--log-handler aeat:DEBUG' in Odoo command line
    debug = False
    taxes_sale = {}
    taxes_purchase = {}
    taxes_result = {}

    def with_context(self, *args, **kwargs):
        context = dict(args[0] if args else self.env.context, **kwargs)
        self.env = self.env(context=context)
        return self

    def _chart_of_accounts_create(self):
        _logger.debug('Creating chart of account')
        self.company = self.env['res.company'].create({
            'name': 'Spanish test company',
        })
        self.chart = self.env.ref('l10n_es.account_chart_template_pymes')
        self.env.ref('base.group_multi_company').write({
            'users': [(4, self.env.uid)],
        })
        self.env.user.write({
            'company_ids': [(4, self.company.id)],
            'company_id': self.company.id,
        })
        self.with_context(
            company_id=self.company.id, force_company=self.company.id)
        wizard = self.env['wizard.multi.charts.accounts'].create({
            'company_id': self.company.id,
            'chart_template_id': self.chart.id,
            'code_digits': 6,
            'currency_id': self.ref('base.EUR'),
            'transfer_account_id': self.chart.transfer_account_id.id,
        })
        wizard.onchange_chart_template_id()
        wizard.execute()
        return True

    def _accounts_search(self):
        _logger.debug('Searching accounts')
        codes = {'472000', '473000', '477000', '475100', '475000',
                 '600000', '700000', '430000', '410000'}
        for code in codes:
            self.accounts[code] = self.env['account.account'].search([
                ('company_id', '=', self.company.id),
                ('code', '=', code),
            ])
        return True

    def _print_move_lines(self, lines):
        _logger.debug(
            '%8s %9s %9s %14s %s',
            'ACCOUNT', 'DEBIT', 'CREDIT', 'TAX', 'TAXES')
        for line in lines:
            _logger.debug(
                '%8s %9s %9s %14s %s',
                line.account_id.code, line.debit, line.credit,
                line.tax_line_id.description,
                line.tax_ids.mapped('description'))

    def _print_tax_lines(self, lines):
        for line in lines:
            _logger.debug(
                "=== [%s] ============================= [%s]",
                line.field_number, line.amount)
            self._print_move_lines(line.move_line_ids)

    def _invoice_sale_create(self, dt):
        data = {
            'company_id': self.company.id,
            'partner_id': self.customer.id,
            'date_invoice': dt,
            'type': 'out_invoice',
            'account_id': self.customer.property_account_receivable_id.id,
            'journal_id': self.journal_sale.id,
            'invoice_line_ids': [],
        }
        _logger.debug('Creating sale invoice: date = %s' % dt)
        if self.debug:
            _logger.debug('%14s %9s' % ('SALE TAX', 'PRICE'))
        for desc, values in self.taxes_sale.iteritems():
            if self.debug:
                _logger.debug('%14s %9s' % (desc, values[0]))
            tax = self.env['account.tax'].search([
                ('company_id', '=', self.company.id),
                ('description', '=', desc),
            ])
            data['invoice_line_ids'].append((0, 0, {
                'name': 'Test for tax %s' % desc,
                'account_id': self.accounts['700000'].id,
                'price_unit': values[0],
                'quantity': 1,
                'invoice_line_tax_ids': [(6, 0, [tax.id])],
            }))
        inv = self.env['account.invoice'].create(data)
        inv.signal_workflow('invoice_open')
        if self.debug:
            self._print_move_lines(inv.move_id.line_ids)
        return inv

    def _invoice_purchase_create(self, dt):
        data = {
            'company_id': self.company.id,
            'partner_id': self.supplier.id,
            'date_invoice': dt,
            'type': 'in_invoice',
            'account_id': self.customer.property_account_payable_id.id,
            'journal_id': self.journal_purchase.id,
            'invoice_line_ids': [],
        }
        _logger.debug('Creating purchase invoice: date = %s' % dt)
        if self.debug:
            _logger.debug('%14s %9s' % ('PURCHASE TAX', 'PRICE'))
        for desc, values in self.taxes_purchase.iteritems():
            if self.debug:
                _logger.debug('%14s %9s' % (desc, values[0]))
            tax = self.env['account.tax'].search([
                ('company_id', '=', self.company.id),
                ('description', '=', desc),
            ])
            data['invoice_line_ids'].append((0, 0, {
                'name': 'Test for tax %s' % tax,
                'account_id': self.accounts['600000'].id,
                'price_unit': values[0],
                'quantity': 1,
                'invoice_line_tax_ids': [(6, 0, [tax.id])],
            }))
        inv = self.env['account.invoice'].create(data)
        inv.signal_workflow('invoice_open')
        if self.debug:
            self._print_move_lines(inv.move_id.line_ids)
        return inv

    def _invoice_refund(self, invoice, dt):
        _logger.debug('Refund %s invoice: date = %s' % (invoice.type, dt))
        inv = invoice.refund(date_invoice=dt, journal_id=self.journal_misc.id)
        inv.signal_workflow('invoice_open')
        if self.debug:
            self._print_move_lines(inv.move_id.line_ids)
        return inv

    def _journals_create(self):
        self.journal_sale = self.env['account.journal'].create({
            'company_id': self.company.id,
            'name': 'Test journal for sale',
            'type': 'sale',
            'code': 'TSALE',
            'default_debit_account_id': self.accounts['700000'].id,
            'default_credit_account_id': self.accounts['700000'].id,
        })
        self.journal_purchase = self.env['account.journal'].create({
            'company_id': self.company.id,
            'name': 'Test journal for purchase',
            'type': 'purchase',
            'code': 'TPUR',
            'default_debit_account_id': self.accounts['600000'].id,
            'default_credit_account_id': self.accounts['600000'].id,
        })
        self.journal_misc = self.env['account.journal'].create({
            'company_id': self.company.id,
            'name': 'Test journal for miscellanea',
            'type': 'general',
            'code': 'TMISC',
        })
        return True

    def _partners_create(self):
        self.customer = self.env['res.partner'].create({
            'company_id': self.company.id,
            'name': 'Test customer',
            'customer': True,
            'supplier': False,
            'property_account_payable_id': self.accounts['410000'].id,
            'property_account_receivable_id': self.accounts['430000'].id,
        })
        self.supplier = self.env['res.partner'].create({
            'company_id': self.company.id,
            'name': 'Test supplier',
            'customer': False,
            'supplier': True,
            'property_account_payable_id': self.accounts['410000'].id,
            'property_account_receivable_id': self.accounts['430000'].id,
        })
        self.customer_bank = self.env['res.partner.bank'].create({
            'partner_id': self.customer.id,
            'acc_number': 'ES66 2100 0418 4012 3456 7891',
        })
        return True

    def setUp(self):
        super(TestL10nEsAeatModBase, self).setUp()
        # Create chart
        self._chart_of_accounts_create()
        # Create accounts
        self._accounts_search()
        # Create journals
        self._journals_create()
        # Create partners
        self._partners_create()
