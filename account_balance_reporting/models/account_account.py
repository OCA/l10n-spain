# -*- coding: utf-8 -*-
# © 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl-3.0).

from openerp import fields, models


class AccountAccount(models.Model):
    _inherit = 'account.account'

    not_level_expand = fields.Boolean(
        string="Don't show this account on financial reports level detail",
        help="If you mark this field, when expanding account balances by "
             "levels on financial reports, this account won't be shown. This "
             "only serves when displaying the account itself, but not when "
             "showing parent accounts, which will include this account "
             "balance as part of the result.")
