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


class L10nEsVatBookIssuedTaxSummary(models.Model):
    _name = 'l10n.es.vat.book.issued.tax.summary'

    tax_code_id = fields.Many2one(
        comodel_name='account.tax.code',
        string=_('Account Tax Code'),
        required=True,
        ondelete="cascade")

    sum_tax_amount = fields.Float(
        string=_('Summary tax amount'))

    sum_base_amount = fields.Float(
        string=_('Summary base amount'))

    tax_percent = fields.Float(
        string=_('Tax percent'))

    vat_book_id = fields.Many2one(
        comodel_name='l10n.es.vat.book',
        string=_('Libro de IVA'))
