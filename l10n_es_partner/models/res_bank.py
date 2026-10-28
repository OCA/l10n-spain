# Copyright 2009 Jordi Esteve <jesteve@zikzakmedia.com>
# Copyright 2012-2014 Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2016-2017 Tecnativa - Pedro M. Baeza
# Copyright 2017 Tecnativa - Carlos Dauden <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3).

from odoo import fields, models


class L10nEsBank(models.Model):
    _name = "l10n.es.bank"
    _description = "Spanish Bank"
    _order = "name, code"

    name = fields.Char(required=True)
    lname = fields.Char("Long name", size=128)
    code = fields.Char(index=True, size=4)
    bic = fields.Char("Bank Identifier Code", index=True)
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char()
    city = fields.Char()
    state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="Fed. State",
        domain="[('country_id', '=?', country_id)]",
    )
    country_id = fields.Many2one(comodel_name="res.country")
    email = fields.Char()
    phone = fields.Char()
    active = fields.Boolean(default=True)
    vat = fields.Char("VAT code", size=32, help="Value Added Tax number")
    website = fields.Char(size=64)

    def _get_partner_bank_values(self):
        self.ensure_one()
        return {
            "bank_name": self.name,
            "bank_bic": self.bic or False,
            "street": self.street or False,
            "street2": self.street2 or False,
            "zip": self.zip or False,
            "city": self.city or False,
            "state_id": self.state_id.id or False,
            "country_id": self.country_id.id or False,
        }
