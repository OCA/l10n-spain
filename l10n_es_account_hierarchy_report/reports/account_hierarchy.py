# -*- coding: utf-8 -*-
# Copyright 2017 Joaquin Gutierrez Pedrosa <joaquin@gutierrezweb.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import tools
from odoo import api, fields, models


class AccountHierarchy(models.Model):
    _name = 'account.hierarchy'
    _description = "Account Hierarchy"
    _auto = False
    _order = 'code, name'

    name = fields.Char(
        string='Name',
        readonly=True)
    code = fields.Char(
        string='Code',
        readonly=True)
    move_date = fields.Date(
        string='Date',
        readonly=True)
    account_id = fields.Many2one(
        string='Account',
        comodel_name='account.account',
        store=True,
        readonly=True)
    one_digit = fields.Char(
        string='1 Digit',
        readonly=True)
    two_digit = fields.Char(
        string='2 Digit',
        readonly=True)
    three_digit = fields.Char(
        string='3 Digit',
        readonly=True)
    company_currency_id = fields.Many2one(
        string='Company Currency',
        comodel_name='res.currency',
        readonly=True)
    debit = fields.Monetary(
        string='Debit',
        default=0.0,
        currency_field='company_currency_id',
        readonly=True)
    credit = fields.Monetary(
        string='Credit',
        default=0.0,
        currency_field='company_currency_id',
        readonly=True)
    balance = fields.Monetary(
        string='Balance',
        default=0.0,
        currency_field='company_currency_id',
        readonly=True)
    company_id = fields.Many2one(
        string='Company',
        comodel_name='res.company',
        readonly=True)
    journal_id = fields.Many2one(
        string='Journal',
        comodel_name='account.journal',
        readonly=True)
    user_type_id = fields.Many2one(
        string='User type',
        comodel_name='account.account.type',
        readonly=True)
    state = fields.Selection(
        selection=[('draft', 'Unposted'),
                   ('posted', 'Posted')],
        string='Status',
        default='draft',
        readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'account_hierarchy')
        self.env.cr.execute("""
        CREATE or REPLACE VIEW account_hierarchy as (
            SELECT move_line.id as id,
                 account.code as code,
                 concat_ws(' ',account.code::text, account.name::text) as name,
                 sum(move_line.credit) as credit,
                 sum(move_line.debit) as debit,
                 sum(move_line.balance) as balance,
                 move_line.date as move_date,
                 move_line.account_id as account_id,
                 move_line.company_id as company_id,
                 move_line.company_currency_id as company_currency_id,
                 move_line.journal_id as journal_id,
                 move_line.user_type_id as user_type_id,
                 move.state as state,
                 account.one_digit as one_digit,
                 account.two_digit as two_digit,
                 account.three_digit as three_digit

            FROM account_account AS account
                 LEFT JOIN account_move_line AS move_line
                    ON (move_line.account_id=account.id)
                 LEFT JOIN account_move as move
                    ON (move_line.move_id=move.id)

            GROUP BY move_line.id,
                     account.code,
                     account.name,
                     move_line.date,
                     move_line.account_id,
                     move_line.company_id,
                     move_line.journal_id,
                     move_line.user_type_id,
                     move_line.company_currency_id,
                     account.one_digit,
                     account.two_digit,
                     account.three_digit,
                     move.state
            )""")
