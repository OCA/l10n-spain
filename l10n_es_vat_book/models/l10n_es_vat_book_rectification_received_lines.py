# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2017 Praxya (http://praxya.com/)
#                       Daniel Rodriguez Lijo <drl.9319@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
from openerp import models, fields, _


class L10nEsVatBookRectificationReceivedLines(models.Model):
    _inherit = 'l10n.es.vat.book.issued.lines'
    _name = 'l10n.es.vat.book.rectification.received.lines'

    tax_lines_rectification_received_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.invoice.tax.lines',
        inverse_name='rectification_received_invoice_line_id',
        string=_("Tax Lines"))
