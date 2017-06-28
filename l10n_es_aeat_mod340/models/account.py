# -*- coding: utf-8 -*-
# Copyright 2012 - Acysos S.L. (http://acysos.com)
#                - Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2016 - Tecnativa - Angel Moya <odoo@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class AccountTax(models.Model):
    _inherit = 'account.tax'

    mod340 = fields.Boolean(string='Include in mod340')


class AccountTaxTemplate(models.Model):
    _inherit = 'account.tax.template'

    mod340 = fields.Boolean(string='Include in mod340')
