# -*- coding: utf-8 -*-
# Copyright 2015 AvanzOSC - Ainara Galdona
# Copyright 2015-2017 Tecnativa - Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from openerp import models, api, fields, _


class AccountTaxCode(models.Model):
    _inherit = 'account.tax.code'

    is_special_prorrate_code = fields.Boolean(
        string='Es de prorrata especial')


class AccountTaxCodeTemplate(models.Model):
    _inherit = 'account.tax.code.template'

    is_special_prorrate_code = fields.Boolean(
        string='Es de prorrata especial')
