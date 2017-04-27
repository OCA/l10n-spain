# -*- coding: utf-8 -*-
# Copyright 2017 Joaquin Gutierrez Pedrosa <joaquin@gutierrezweb.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID
from odoo.api import Environment


def post_init_hook(cr, pool):
    env = Environment(cr, SUPERUSER_ID, {})
    accounts = env['account.account'].search([])
    for account in accounts:
        label_one = env['account.hierarchy.label'].search([
            ('level', '=', 1), ('code', '=', account.code[0])])
        account.one_digit = '%s %s' % (
            account.code[0], label_one and label_one.name or '')
        label_two = env['account.hierarchy.label'].search([
            ('level', '=', 2), ('code', '=', account.code[0:2])])
        account.two_digit = '%s %s' % (
            account.code[0:2], label_two and label_two.name or '')
        label_three = env['account.hierarchy.label'].search([
            ('level', '=', 3), ('code', '=', account.code[0:3])])
        account.three_digit = '%s %s' % (
            account.code[0:3], label_three and label_three.name or '')
