# Copyright 2020 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models, fields


class TicketBAIVATExemptionKey(models.Model):
    _name = 'tbai.vat.exemption.key'
    _description = 'TicketBAI VAT Exemption mapping keys'

    code = fields.Char(string='Code', required=True)
    name = fields.Char('Name', required=True)

    @api.multi
    def name_get(self):
        vals = []
        for record in self:
            name = '[{}]-{}'.format(record.code, record.name)
            vals.append(tuple([record.id, name]))
        return vals
