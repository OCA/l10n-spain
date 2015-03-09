# -*- coding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import fields, models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.one
    @api.depends('cc_amount_untaxed', 'tax_line.amount')
    def _get_amount_total_wo_irpf(self):
        self.amount_total_wo_irpf = self.cc_amount_untaxed
        for tax_line in self.tax_line:
            if 'IRPF' not in tax_line.name:
                self.amount_total_wo_irpf += tax_line.amount

    amount_total_wo_irpf = fields.Float(
        compute="_get_amount_total_wo_irpf",
        string="Total amount without IRPF taxes")
