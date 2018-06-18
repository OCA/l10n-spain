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
from openerp import models, fields


class L10nEsVatBookIssuedLines(models.Model):
    _name = 'l10n.es.vat.book.issued.lines'
    _order = 'invoice_id desc'

    invoice_date = fields.Date(
        string='Invoice Date')

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Empresa')

    vat_number = fields.Char(
        string='NIF')

    invoice_id = fields.Many2one(
        comodel_name='account.invoice',
        string='Invoice')

    base = fields.Float(
        string='Base')

    tax_import = fields.Float(
        string='Tax import')

    total = fields.Float(
        string='Total')

    l10n_es_vat_book_id = fields.Many2one(
        comodel_name='l10n.es.vat.book',
        string='Vat Book id')

    tax_line_issued_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.invoice.tax.lines',
        inverse_name='issued_invoice_line_id',
        string="Lineas de impuesto")

    exeption = fields.Boolean(
        string="Exeption")

    exeption_text = fields.Char(
        string="Exeption text")
