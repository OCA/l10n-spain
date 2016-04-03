# -*- coding: utf-8 -*-
# © 2009 Jordi Esteve <jesteve@zikzakmedia.com>
# © 2012-2014 Ignacio Ibeas <ignacio@acysos.com>
# © 2016 Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl-3).

from openerp import models, fields


class ResBank(models.Model):
    _inherit = 'res.bank'

    code = fields.Char('Code', size=64)
    lname = fields.Char('Long name', size=128)
    vat = fields.Char('VAT code', size=32, help='Value Added Tax number')
    website = fields.Char('Website', size=64)
