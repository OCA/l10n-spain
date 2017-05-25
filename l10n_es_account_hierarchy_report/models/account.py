# -*- coding: utf-8 -*-
# Copyright 2017 Joaquin Gutierrez Pedrosa <joaquin@gutierrezweb.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class AccountAccount(models.Model):
    _inherit = 'account.account'

    @api.depends('name', 'code', 'user_type_id', 'internal_type', 'reconcile')
    @api.multi
    def _compute_digits(self):
        for account in self:
            label_one = self.env['account.hierarchy.label'].search([
                ('level', '=', 1), ('code', '=', account.code[0])])
            account.one_digit = '%s %s' % (
                account.code[0], label_one and label_one.name or '')
            label_two = self.env['account.hierarchy.label'].search([
                ('level', '=', 2), ('code', '=', account.code[0:2])])
            account.two_digit = '%s %s' % (
                account.code[0:2], label_two and label_two.name or '')
            label_three = self.env['account.hierarchy.label'].search([
                ('level', '=', 3), ('code', '=', account.code[0:3])])
            account.three_digit = '%s %s' % (
                account.code[0:3], label_three and label_three.name or '')

    one_digit = fields.Char(
        string='1 Digit',
        compute='_compute_digits',
        store=True,
        help="One Digit")
    two_digit = fields.Char(
        string='2 Digit',
        compute='_compute_digits',
        store=True,
        help="Two Digit")
    three_digit = fields.Char(
        string='3 Digit',
        compute='_compute_digits',
        store=True,
        help="Three Digit")
