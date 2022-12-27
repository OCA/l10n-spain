# Copyright 2009 Jordi Esteve <jesteve@zikzakmedia.com>
# Copyright 2012-2014 Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2016-2017 Tecnativa - Pedro M. Baeza
# Copyright 2017 Tecnativa - Carlos Dauden <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3).

from odoo import fields, models


class ResBank(models.Model):
    _inherit = "res.bank"

    lname = fields.Char("Long name", size=128)
    vat = fields.Char("VAT code", size=32, help="Value Added Tax number")
    website = fields.Char(size=64)
