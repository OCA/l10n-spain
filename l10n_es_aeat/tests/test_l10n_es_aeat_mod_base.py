# -*- coding: utf-8 -*-
# © 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

import logging
from odoo.tests import common

_logger = logging.getLogger('aeat')


@common.at_install(False)
@common.post_install(True)
class TestL10nEsAeatModBase(common.TransactionCase):
    accounts = {}
    # Set 'debug' attribute to True to easy debug this test
    # Do not forget to include '--log-handler aeat:DEBUG' in Odoo command line
    debug = False
    # These 2 dictionaries below allows to define easily several taxes to apply
    # to invoice lines through the methods _invoice_sale/purchase_create.
    # The structure is:
    # * One dictionary entry per invoice line.
    # * The key of the entry will be the code of the tax.
    # * You can duplicate invoice lines with the same tax using a suffix '//X',
    #   being X any string.
    # * You can include more than one tax in the same invoice line, splitting
    #   each tax code by a comma.
    # * The value of the entry will be a list, being the first element of the
    #   the list, the price_unit amount. The rest of the elements can be for
    #   reference, but not used, like the tax amount in second position.
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

    def _invoice_sale_create(self, dt, extra_vals=None):
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
        for desc, values in self.taxes_sale.items():
            if self.debug:
                _logger.debug('%14s %9s' % (desc, values[0]))
            # Allow to duplicate taxes skipping the unique key constraint
            descs = desc.split('//')[0]
            line_data = {
                'name': 'Test for tax(es) %s' % descs,
                'account_id': self.accounts['700000'].id,
                'price_unit': values[0],
                'quantity': 1,
                'invoice_line_tax_ids': [],
            }
            for desc in descs.split(','):
                tax = self.env['account.tax'].search([
                    ('company_id', '=', self.company.id),
                    ('description', '=', desc),
                ])
                if tax:
                    line_data['invoice_line_tax_ids'].append((4, tax.id))
                else:
                    _logger.error("Tax not found: {}".format(desc))
            data['invoice_line_ids'].append((0, 0, line_data))
        if extra_vals:
            data.update(extra_vals)
        inv = self.env['account.invoice'].sudo(self.billing_user).create(data)
        inv.action_invoice_open()
        if self.debug:
            self._print_move_lines(inv.move_id.line_ids)
        return inv

    def _invoice_purchase_create(self, dt, extra_vals=None):
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
        for desc, values in self.taxes_purchase.items():
            if self.debug:
                _logger.debug('%14s %9s' % (desc, values[0]))
            # Allow to duplicate taxes skipping the unique key constraint
            descs = desc.split('//')[0]
            line_data = {
                'name': 'Test for tax(es) %s' % descs,
                'account_id': self.accounts['600000'].id,
                'price_unit': values[0],
                'quantity': 1,
                'invoice_line_tax_ids': [],
            }
            for desc in descs.split(','):
                tax = self.env['account.tax'].search([
                    ('company_id', '=', self.company.id),
                    ('description', '=', desc),
                ])
                if tax:
                    line_data['invoice_line_tax_ids'].append((4, tax.id))
                else:
                    _logger.error("Tax not found: {}".format(desc))
            data['invoice_line_ids'].append((0, 0, line_data))
        if extra_vals:
            data.update(extra_vals)
        inv = self.env['account.invoice'].sudo(self.billing_user).create(data)
        inv.action_invoice_open()
        if self.debug:
            self._print_move_lines(inv.move_id.line_ids)
        return inv

    def _invoice_refund(self, invoice, dt):
        _logger.debug('Refund %s invoice: date = %s' % (invoice.type, dt))
        inv = invoice.sudo(self.billing_user).refund(
            date_invoice=dt, journal_id=self.journal_misc.id)
        inv.action_invoice_open()
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
        self.journal_cash = self.env['account.journal'].create({
            'company_id': self.company.id,
            'name': 'Test journal for cash',
            'type': 'cash',
            'code': 'TCSH',
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

        invocing_grp = self.env.ref('account.group_account_invoice')
        account_user_grp = self.env.ref('account.group_account_user')
        account_manager_grp = self.env.ref('account.group_account_manager')
        aeat_grp = self.env.ref('l10n_es_aeat.group_account_aeat')

        # Create test user
        Users = self.env['res.users'].with_context(
            {'no_reset_password': True, 'mail_create_nosubscribe': True})
        self.billing_user = Users.create({
            'name': 'Billing user',
            'login': 'billing_user',
            'email': 'billing.user@example.com',
            'groups_id': [(6, 0, [invocing_grp.id])]})
        self.account_user = Users.create({
            'name': 'Account user',
            'login': 'account_user',
            'email': 'account.user@example.com',
            'groups_id': [(6, 0, [account_user_grp.id])]})
        self.account_manager = Users.create({
            'name': 'Account manager',
            'login': 'account_manager',
            'email': 'account.manager@example.com',
            'groups_id': [(6, 0, [account_manager_grp.id, aeat_grp.id])]})
