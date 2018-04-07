# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2017 Praxya (http://praxya.com/)
#                       Daniel Rodriguez Lijo <drl.9319@gmail.com>
#                       Ignacio Ibeas <ignacio@acysos.com>
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
from openerp import models, api, fields, _
from openerp.exceptions import Warning as UserError


VALID_TYPES = [
    0, 0.005, 0.014, 0.04, 0.052, 0.07, 0.08, 0.10, 0.12, 0.16, 0.18, 0.21
]


class L10nEsVatBook(models.Model):
    _inherit = "l10n.es.aeat.report"
    _name = 'l10n.es.vat.book'
    _period_quarterly = True
    _period_monthly = True
    _period_yearly = True

    number = fields.Char(
        default="vat_book",
        readonly="True")

    issued_invoice_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.issued.lines',
        inverse_name='l10n_es_vat_book_id',
        string='Issued invoices',
        readonly="True")

    received_invoice_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.received.lines',
        inverse_name='l10n_es_vat_book_id',
        string='Received received',
        readonly="True")

    rectification_issued_invoice_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.rectification.issued.lines',
        inverse_name='l10n_es_vat_book_id',
        string='Rectification issued',
        readonly="True")

    rectification_received_invoice_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.rectification.received.lines',
        inverse_name='l10n_es_vat_book_id',
        string='Rectification received',
        readonly="True")

    calculation_date = fields.Date(
        string='Calculation Date')

    amount_without_tax_issued = fields.Float(
        string='Total without taxes',
        readonly="True")

    amount_tax_issued = fields.Float(
        string='Taxes',
        readonly="True")

    amount_total_issued = fields.Float(
        string='Total',
        readonly="True")

    issued_tax_summary = fields.One2many(
        comodel_name='l10n.es.vat.book.issued.tax.summary',
        inverse_name='vat_book_id',
        string="Issued tax summary",
        readonly="True")

    amount_without_tax_received = fields.Float(
        string='Total without taxes',
        readonly="True")

    amount_tax_received = fields.Float(
        string='Taxes',
        readonly="True")

    amount_total_received = fields.Float(
        string='Total',
        readonly="True")

    received_tax_summary = fields.One2many(
        comodel_name='l10n.es.vat.book.received.tax.summary',
        inverse_name='vat_book_id',
        string="Received tax summary",
        readonly="True")

    amount_without_tax_rectification_issued = fields.Float(
        string='Total without taxes',
        readonly="True")

    amount_tax_rectification_issued = fields.Float(
        string='Taxes',
        readonly="True")

    amount_total_rectification_issued = fields.Float(
        string='Total',
        readonly="True")

    rectification_issued_tax_summary = fields.One2many(
        comodel_name='l10n.es.vat.book.rectification.issued.tax.summary',
        inverse_name='vat_book_id',
        string="Issued tax summary",
        readonly="True")

    amount_without_tax_rectification_received = fields.Float(
        string='Total without taxes',
        readonly="True")

    amount_tax_rectification_received = fields.Float(
        string='Taxes',
        readonly="True")

    amount_total_rectification_received = fields.Float(
        string='Total',
        readonly="True")

    rectification_received_tax_summary = fields.One2many(
        comodel_name='l10n.es.vat.book.rectification.received.tax.summary',
        inverse_name='vat_book_id',
        string="Received tax summary",
        readonly="True")

    @api.multi
    def button_calculate(self):
        """
            Funcion call from vat_book
        """
        self._calculate_vat_book()
        return True

    def nearby(self, final, numbers):
        """
            Inerhit from mod 340
            Author: XASSIZ
        """
        def minor(numbers):
            minor = numbers[0]
            result = 0
            for x in range(len(numbers)):
                if numbers[x] < minor:
                    minor = numbers[x]
                    result = x
            return result

        difference = []
        for x in range(len(numbers)):
            difference.append(abs(final - numbers[x]))
        return numbers[minor(difference)]

    def _get_vals_invoice_line(self, invoice_id):
        """
            This function make the dictionary to create a new record in issued
            invoices, Received invoices or rectification invoices

            Args:
                invoice_id (obj): invoice

            Returns:
                dictionary: Vals from the new record.
        """
        values = {
            'invoice_date': invoice_id.date_invoice,
            'partner_id': invoice_id.partner_id.id,
            'vat_number': invoice_id.partner_id.vat,
            'invoice_id': invoice_id.id,
            'base': invoice_id.amount_untaxed,
            'tax_import': invoice_id.amount_tax,
            'total': invoice_id.amount_total,
            'l10n_es_vat_book_id': self.id,
        }
        return values

    def _create_new_invoice_line(self, invoice_id):
        """
            This function create a new record in issued invoices, Received
            invoices or rectification invoices

            Args:
                invoice_id (obj): invoice

            Returns:
                obj: obj with new object create depends invoice type.
        """
        issued_invoice_obj = self.env['l10n.es.vat.book.issued.lines']
        received_invoice_obj = self.env['l10n.es.vat.book.received.lines']
        rectification_issued_invoice_obj =\
            self.env['l10n.es.vat.book.rectification.issued.lines']
        rectification_received_invoice_obj =\
            self.env['l10n.es.vat.book.rectification.received.lines']
        new_record = False
        invoice_vals = self._get_vals_invoice_line(invoice_id)
        exeption_text = ""
        exeption = False
        if invoice_id.amount_total == 0:
            exeption = True
            exeption_text = _("The invoice can't have 0 in total \n")
        if not invoice_id.partner_id.vat:
            exeption = True
            exeption_text += _("¡The partner haven't VAT!")

        if exeption:
            invoice_vals.update({
                'exeption': True,
                'exeption_text': exeption_text,
            })
        if invoice_id.type in ('out_invoice'):
            new_record = issued_invoice_obj.create(invoice_vals)
        elif invoice_id.type in ('in_invoice'):
            new_record = received_invoice_obj.create(invoice_vals)
        elif invoice_id.type in ('out_refund'):
            new_record = rectification_issued_invoice_obj.create(invoice_vals)
        elif invoice_id.type in ('in_refund'):
            new_record =\
                rectification_received_invoice_obj.create(invoice_vals)
        return new_record

    def _vals_invoice_tax(self, invoice_tax_line):
        """
            This function return a dictionary to create a new
            l10n.es.vat.book.invoice.tax.lines

            Args:
                invoice_tax_line (obj): account.invoice.tax

            Returns:
                bool: True if successful, False otherwise.
        """
        tax_percentage = 0
        if invoice_tax_line.amount > 0 and invoice_tax_line.base > 0:
            tax_percentage = self.nearby(
                round(abs(invoice_tax_line.amount / invoice_tax_line.base), 4),
                VALID_TYPES,
            )
        vals = {
            'name': invoice_tax_line.name,
            'tax_percent': tax_percentage,
            'tax_amount': invoice_tax_line.amount,
            'amount_without_tax': invoice_tax_line.base,
        }
        return vals

    def _create_invoice_tax(self,
                            invoice_vat_book_line_id,
                            invoice_id,
                            tax_code_ids):
        """
            This function create a l10n.es.vat.book.invoice.tax.lines for the
            current issued invoice, Received Invoices, Rectification invoices

            Args:
                invoice_vat_book_line_id (obj): l10n.es.vat.book.issued.lines
                or l10n.es.vat.book.received.lines or
                l10n.es.vat.book.rectification.lines
                invoice_id (obj): Invoice
                tax_code_ids (obj): account.tax.code from the vat book
            Returns:
                bool: True if successful, False otherwise.
        """
        invoice_tax_lines_obj = self.env['l10n.es.vat.book.invoice.tax.lines']
        for invoice_tax_line in invoice_id.tax_line:
            tax_code = invoice_tax_line.mapped('base_code_id.id')
            # If this tax be in the vat_book tax list create a new tax line
            if tax_code != [] and set(tax_code) < set(tax_code_ids.ids):
                vals = self._vals_invoice_tax(invoice_tax_line)
                if invoice_id.type in ('out_invoice'):
                    vals.update({
                        'issued_invoice_line_id': invoice_vat_book_line_id.id
                    })
                    invoice_tax_lines_obj.create(vals)
                elif invoice_id.type in ('in_invoice'):
                    vals.update({
                        'received_invoice_line_id': invoice_vat_book_line_id.id
                    })
                    invoice_tax_lines_obj.create(vals)
                elif invoice_id.type in ('out_refund'):
                    vals.update({
                        'rectification_issued_invoice_line_id':
                        invoice_vat_book_line_id.id
                    })
                    invoice_tax_lines_obj.create(vals)
                elif invoice_id.type in ('in_refund'):
                    vals.update({
                        'rectification_received_invoice_line_id':
                        invoice_vat_book_line_id.id
                    })
                    invoice_tax_lines_obj.create(vals)

                # Update summary
                self._invoices_summary(invoice_tax_line, invoice_id.type)

    def _get_vals_summary_invoices(self, tax_code, invoice_tax_line):
        """
            This function return a dictionary from the values to create or
            update a summery tax line

            Args:
                tax_code (int): tax_code id
                invoice_tax_line (obj): account.invoice.tax

            Returns:
                vals: values to create a summary tax line
        """
        if invoice_tax_line.amount > 0 and invoice_tax_line.base > 0:
            tax_percentage = self.nearby(
                round(abs(invoice_tax_line.amount / invoice_tax_line.base), 4),
                VALID_TYPES,
            )
        else:
            tax_percentage = 0
        vals = {
            'tax_code_id': tax_code,
            'sum_tax_amount': invoice_tax_line.amount,
            'sum_base_amount': invoice_tax_line.base,
            'tax_percent': tax_percentage,
            'vat_book_id': self.id,
        }
        return vals

    def _invoices_summary(self, invoice_tax_line, invoice_type):
        """
            This function sum to the summary the value of new tax

            Args:
                invoice_tax_line (obj): account.invoice.tax
                invoice_type (str): out_invoice, in_invoice, out_refund,
                in_refund

            Returns:
                bool: True if successful, False otherwise.
        """
        issued_tax_summary_obj =\
            self.env['l10n.es.vat.book.issued.tax.summary']
        received_tax_summary_obj =\
            self.env['l10n.es.vat.book.received.tax.summary']
        rectification_issued_tax_summary_obj =\
            self.env['l10n.es.vat.book.rectification.issued.tax.summary']
        rectification_received_tax_summary_obj =\
            self.env['l10n.es.vat.book.rectification.received.tax.summary']
        tax_code = invoice_tax_line.mapped('base_code_id.id')

        if invoice_type in ('out_invoice'):
            self.write({
                'amount_without_tax_issued':
                    self.amount_without_tax_issued + invoice_tax_line.base,
                'amount_tax_issued':
                    self.amount_tax_issued + invoice_tax_line.amount,
                'amount_total_issued':
                    self.amount_total_issued + (invoice_tax_line.base +
                                                invoice_tax_line.amount),
            })

            # return the actually tax lines
            tax_lines = self.issued_tax_summary.mapped('tax_code_id.id')
            # If this tax not here make a new line, if this tax exist Add
            # the new amount
            if tax_code[0] in tax_lines:
                issued_tax_summary_id = issued_tax_summary_obj.search([
                    ('tax_code_id', 'in', tax_code),
                    ('vat_book_id', '=', self.id),
                ])
                issued_tax_summary_id.write({
                    'sum_tax_amount': issued_tax_summary_id.sum_tax_amount +
                    invoice_tax_line.amount,
                    'sum_base_amount': issued_tax_summary_id.sum_base_amount +
                    invoice_tax_line.base,
                })
            else:
                vals = self._get_vals_summary_invoices(
                    tax_code[0], invoice_tax_line)
                issued_tax_summary_obj.create(vals)
        elif invoice_type in ('in_invoice'):
            self.write({
                'amount_without_tax_received':
                    self.amount_without_tax_received + invoice_tax_line.base,
                'amount_tax_received':
                    self.amount_tax_received + invoice_tax_line.amount,
                'amount_total_received':
                    self.amount_total_received + (invoice_tax_line.base +
                                                  invoice_tax_line.amount),
            })

            # return the actually tax lines
            tax_lines = self.received_tax_summary.mapped('tax_code_id.id')
            # If this tax not here make a new line, if this tax exist Add
            # the new amount
            if tax_code[0] in tax_lines:
                received_tax_summary_id = received_tax_summary_obj.search([
                    ('tax_code_id', 'in', tax_code),
                    ('vat_book_id', '=', self.id),
                ])
                received_tax_summary_id.write({
                    'sum_tax_amount': received_tax_summary_id.sum_tax_amount +
                    invoice_tax_line.amount,
                    'sum_base_amount':
                    received_tax_summary_id.sum_base_amount +
                    invoice_tax_line.base,
                })
            else:
                vals = self._get_vals_summary_invoices(
                    tax_code[0], invoice_tax_line)
                received_tax_summary_obj.create(vals)
        elif invoice_type in ('out_refund'):
            self.write({
                'amount_without_tax_rectification_issued':
                    self.amount_without_tax_rectification_issued +
                    invoice_tax_line.base,
                'amount_tax_rectification_issued':
                    self.amount_tax_rectification_issued +
                    invoice_tax_line.amount,
                'amount_total_rectification_issued':
                    self.amount_total_rectification_issued +
                    (invoice_tax_line.base + invoice_tax_line.amount),
            })

            # return the actually tax lines
            tax_lines =\
                self.rectification_issued_tax_summary.mapped('tax_code_id.id')
            # If this tax not here make a new line, if this tax exist Add
            # the new amount
            if tax_code[0] in tax_lines:
                rectification_issued_tax_summary_id =\
                    rectification_issued_tax_summary_obj.search([
                        ('tax_code_id', 'in', tax_code),
                        ('vat_book_id', '=', self.id),
                    ])
                rectification_issued_tax_summary_id.write({
                    'sum_tax_amount':
                    rectification_issued_tax_summary_id.sum_tax_amount +
                    invoice_tax_line.amount,
                    'sum_base_amount':
                    rectification_issued_tax_summary_id.sum_base_amount +
                    invoice_tax_line.base,
                })
            else:
                vals = self._get_vals_summary_invoices(
                    tax_code[0], invoice_tax_line)
                rectification_issued_tax_summary_obj.create(vals)
        elif invoice_type in ('in_refund'):
            self.write({
                'amount_without_tax_rectification_received':
                    self.amount_without_tax_rectification_received +
                    invoice_tax_line.base,
                'amount_tax_rectification_received':
                    self.amount_tax_rectification_received +
                    invoice_tax_line.amount,
                'amount_total_rectification_received':
                    self.amount_total_rectification_received +
                    (invoice_tax_line.base + invoice_tax_line.amount),
            })

            # return the actually tax lines
            tax_lines =\
                self.rectification_received_tax_summary.mapped(
                    'tax_code_id.id')
            # If this tax not here make a new line, if this tax exist Add
            # the new amount
            if tax_code[0] in tax_lines:
                rectification_received_tax_summary_id =\
                    rectification_received_tax_summary_obj.search([
                        ('tax_code_id', 'in', tax_code),
                        ('vat_book_id', '=', self.id),
                    ])
                rectification_received_tax_summary_id.write({
                    'sum_tax_amount':
                    rectification_received_tax_summary_id.sum_tax_amount +
                    invoice_tax_line.amount,
                    'sum_base_amount':
                    rectification_received_tax_summary_id.sum_base_amount +
                    invoice_tax_line.base,
                })
            else:
                vals = self._get_vals_summary_invoices(
                    tax_code[0], invoice_tax_line)
                rectification_received_tax_summary_obj.create(vals)

    def _clear_old_data(self):
        """
            This function clean all the old data to make a new calculation
        """
        self.issued_invoice_ids.unlink()
        self.received_invoice_ids.unlink()
        self.rectification_issued_invoice_ids.unlink()
        self.rectification_received_invoice_ids.unlink()
        self.amount_without_tax_issued = 0
        self.amount_tax_issued = 0
        self.amount_total_issued = 0
        self.issued_tax_summary.unlink()
        self.amount_without_tax_received = 0
        self.amount_tax_received = 0
        self.amount_total_received = 0
        self.received_tax_summary.unlink()
        self.amount_without_tax_rectification_issued = 0
        self.amount_tax_rectification_issued = 0
        self.amount_total_rectification_issued = 0
        self.rectification_issued_tax_summary.unlink()
        self.amount_without_tax_rectification_received = 0
        self.amount_tax_rectification_received = 0
        self.amount_total_rectification_received = 0
        self.rectification_received_tax_summary.unlink()

    def _calculate_vat_book(self):
        """
            This function calculate all the taxes, from issued invoices,
            received invoices and rectification invoices
        """
        invoice_obj = self.env['account.invoice']
        tax_code_obj = self.env['account.tax.code']
        if not self.company_id.partner_id.vat:
            raise UserError(
                _("This company doesn't have NIF"))

        # clean the old invoice records
        self._clear_old_data()

        # Get all the invoices in state different to fradt an cancel
        domain = [
            ('period_id', 'in', self.periods.ids),
            ('state', 'in', ('open', 'paid'))
        ]
        invoice_ids = invoice_obj.search(domain)

        # Obtain Map code template from vat_book
        tax_code_vat_book = self.env.ref(
            'l10n_es_vat_book.aeat_vat_book_line_01')
        # Obtain all the codes from account.tax.code.template
        tax_codes_template = tax_code_vat_book.mapped('tax_codes.code')
        # search the account.tax.code referent to account.tax.code.template
        tax_code_ids = tax_code_obj.search([
            ('code', 'in', tax_codes_template),
            ('company_id', 'child_of', self.company_id.id)
        ])

        for invoice_id in invoice_ids:
            # Obtain all account.tax.code id inside a invoice
            invoice_tax_code_ids = \
                invoice_id.tax_line.mapped('base_code_id.id')

            # If the account.tax.code from the invoice are not in the list of
            # account.tax.code vat book this invoice can't be in the vat_book
            vat_ok = False
            for elem in invoice_tax_code_ids:
                if elem in tax_code_ids.ids:
                    vat_ok = True
                    break
            # If any of invoice tax are in vat_book list continue to the next
            # invoice
            if not vat_ok:
                continue

            # Create a issued, received or rectification invoice line
            invoice_vat_book_line_id = \
                self._create_new_invoice_line(invoice_id)

            # Create tax lines for the current vat_book_line
            self._create_invoice_tax(
                invoice_vat_book_line_id, invoice_id, tax_code_ids)
        # Write state and date in the report
        self.write({
            'state': 'calculated',
            'calculation_date': fields.Datetime.now(),
        })

    def __init__(self, pool, cr):
        self._aeat_number = 'vat_book'
        super(L10nEsVatBook, self).__init__(pool, cr)
