# -*- coding: utf-8 -*-
# Copyright 2017 Praxya (http://praxya.com/)
#                Daniel Rodriguez Lijo <drl.9319@gmail.com>
# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
#                <contact@eficent.com>
# Copyright 2018 Luis M. Ontalba <luismaront@gmail.com>
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0
import datetime

from odoo import models, api, fields, _
from odoo.exceptions import Warning as UserError


class L10nEsVatBook(models.Model):
    _name = 'l10n.es.vat.book'
    _inherit = "l10n.es.aeat.report"
    _aeat_number = 'LIVA'
    _period_yearly = True

    number = fields.Char(
        default="vat_book",
        readonly="True")

    line_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.line',
        inverse_name='vat_book_id',
        string='Issued/Received invoices',
        copy=False,
        readonly="True")

    issued_line_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.line',
        inverse_name='vat_book_id',
        domain=[('line_type', '=', 'issued')],
        string='Issued invoices',
        copy=False,
        readonly="True")

    rectification_issued_line_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.line',
        inverse_name='vat_book_id',
        domain=[('line_type', '=', 'rectification_issued')],
        string='Issued Refund Invoices',
        copy=False,
        readonly="True")

    received_line_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.line',
        inverse_name='vat_book_id',
        domain=[('line_type', '=', 'received')],
        string='Received invoices',
        copy=False,
        readonly="True")

    rectification_received_line_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.line',
        inverse_name='vat_book_id',
        domain=[('line_type', '=', 'rectification_received')],
        string='Received Refund Invoices',
        copy=False,
        readonly="True")

    calculation_date = fields.Date(
        string='Calculation Date')

    tax_summary_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.tax.summary',
        string="Tax Summary",
        inverse_name='vat_book_id',
        readonly="True")

    issued_tax_summary_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.tax.summary',
        string="Issued Tax Summary",
        inverse_name='vat_book_id',
        domain=[('book_type', '=', 'issued')],
        readonly="True")

    received_tax_summary_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.tax.summary',
        string="Received Tax Summary",
        inverse_name='vat_book_id',
        domain=[('book_type', '=', 'received')],
        readonly="True")

    summary_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.summary',
        string="Summary",
        inverse_name='vat_book_id',
        readonly="True")

    issued_summary_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.summary',
        string="Issued Summary",
        inverse_name='vat_book_id',
        domain=[('book_type', '=', 'issued')],
        readonly="True")

    received_summary_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.summary',
        string="Received Summary",
        inverse_name='vat_book_id',
        domain=[('book_type', '=', 'received')],
        readonly="True")

    auto_renumber = fields.Boolean('Auto renumber invoices received',
                                   states={'draft': [('readonly', False)]})

    @api.model
    def _prepare_vat_book_tax_summary(self, tax_lines, book_type):
        tax_summary_data_recs = {}
        for tax_line in tax_lines:
            if tax_line.tax_id not in tax_summary_data_recs:
                tax_summary_data_recs[tax_line.tax_id] = {
                    'book_type': book_type,
                    'base_amount': 0.0,
                    'tax_amount': 0.0,
                    'total_amount': 0.0,
                    'tax_id': tax_line.tax_id.id,
                    'vat_book_id': self.id,
                }
            tax_summary_data_recs[tax_line.tax_id]['base_amount'] += \
                tax_line.base_amount
            tax_summary_data_recs[tax_line.tax_id]['tax_amount'] +=  \
                tax_line.tax_amount
            tax_summary_data_recs[tax_line.tax_id]['total_amount'] +=  \
                tax_line.total_amount
        return tax_summary_data_recs

    @api.model
    def _create_vat_book_tax_summary(self, tax_summary_data_recs,
                                     tax_summary):
        for tax_id in tax_summary_data_recs.keys():
            self.env['l10n.es.vat.book.tax.summary'].create(
                tax_summary_data_recs[tax_id])
        return tax_summary

    @api.model
    def _prepare_vat_book_summary(self, tax_summary_recs, book_type):
        base_amount = sum(tax_summary_recs.mapped('base_amount'))
        tax_amount = sum(tax_summary_recs.mapped('tax_amount'))
        total_amount = sum(tax_summary_recs.mapped('total_amount'))
        return {
            'book_type': book_type,
            'base_amount': base_amount,
            'tax_amount': tax_amount,
            'total_amount': total_amount,
            'vat_book_id': self.id,
        }

    @api.model
    def _create_vat_book_summary(self, tax_summary_recs, book_type):
        vals = self._prepare_vat_book_summary(tax_summary_recs, book_type)
        self.env['l10n.es.vat.book.summary'].create(vals)

    @api.multi
    def calculate(self):
        """
            Funcion call from vat_book
        """
        self._calculate_vat_book()
        return True

    def _get_vals_invoice_line(self, move, line_type):
        """
            This function make the dictionary to create a new record in issued
            invoices, Received invoices or rectification invoices

            Args:
                move (obj): move

            Returns:
                dictionary: Vals from the new record.
        """
        ref = move.ref
        ext_ref = ''
        invoice = move.line_ids.mapped('invoice_id')[:1]
        if invoice:
            ref = invoice.number
            ext_ref = invoice.reference
        return {
            'line_type': line_type,
            'invoice_date': move.date,
            'partner_id': move.partner_id.id,
            'vat_number': move.partner_id.vat,
            'invoice_id': invoice.id,
            'ref': ref,
            'external_ref': ext_ref,
            'vat_book_id': self.id,
            'move_id': move.id,
        }

    def _get_vat_book_line_tax(self, tax, move, vat_book_line):
        base_move_lines = move.line_ids.filtered(
            lambda l: any(t == tax for t in l.tax_ids))
        base_amount_untaxed = sum(x.credit - x.debit for x in base_move_lines)

        parent_tax = self.env['account.tax'].search([
            ('children_tax_ids.id', '=', tax.id)], limit=1)
        taxes = self.env['account.tax']
        if parent_tax:
            taxes = tax.children_tax_ids
            tax = parent_tax
        else:
            taxes += tax
        fee_move_lines = move.line_ids.filtered(
            lambda l: l.tax_line_id in taxes)
        fee_amount_untaxed = 0.0
        if fee_move_lines:
            fee_amount_untaxed = sum(
                x.credit - x.debit for x in fee_move_lines)

        if vat_book_line.line_type == 'issued' and fee_amount_untaxed < 0.0:
            vat_book_line.line_type = 'rectification_issued'

        if vat_book_line.line_type == 'received' and fee_amount_untaxed > 0.0:
            vat_book_line.line_type = 'rectification_received'

        if vat_book_line.line_type in ['received', 'rectification_received']:
            base_amount_untaxed *= -1
            fee_amount_untaxed *= -1

        return {
            'tax_id': tax.id,
            'base_amount': base_amount_untaxed,
            'tax_amount': fee_amount_untaxed,
            'total_amount': base_amount_untaxed + fee_amount_untaxed,
            'move_line_ids': [(4, aml.id) for aml
                              in base_move_lines + fee_move_lines],
            'vat_book_line_id': vat_book_line.id,
        }

    def _create_vat_book_line_tax(self, tax, vat_book_line_id,
                                  move):
        vat_book_line_tax_obj = self.env['l10n.es.vat.book.line.tax']
        vals = self._get_vat_book_line_tax(tax, move, vat_book_line_id)

        new_record = vat_book_line_tax_obj.create(vals)

        return new_record

    def _create_vat_book_line(self, move, line_type):
        """
            This function create a new record in issued invoices, Received
            invoices or rectification invoices

            Args:
                move (obj): move

            Returns:
                obj: obj with new object create depends invoice type.
        """
        vat_book_line_obj = self.env['l10n.es.vat.book.line']

        vals = self._get_vals_invoice_line(move, line_type)
        exception_text = ""
        exception = False
        if vals['invoice_id'] and not vals['vat_number']:
            exception = True
            exception_text += _("The partner doesn't have a VAT number")

        if exception:
            vals.update({
                'exception': True,
                'exception_text': exception_text,
            })

        return vat_book_line_obj.create(vals)

    def _clear_old_data(self):
        """
            This function clean all the old data to make a new calculation
        """
        self.line_ids.unlink()
        self.summary_ids.unlink()
        self.tax_summary_ids.unlink()

    def _account_move_line_domain(self, taxes):
        # search move lines that contain these tax codes
        return [('date', '>=', self.date_start),
                ('date', '<=', self.date_end),
                '|', ('tax_ids', 'in', taxes.ids),
                ('tax_line_id', 'in', taxes.ids)]

    def _get_account_moves(self, taxes):
        aml_obj = self.env['account.move.line']
        amls = aml_obj.search(self._account_move_line_domain(taxes))
        return amls.mapped('move_id')

    def _create_vat_book_records(self, move, line_type, taxes):
        line = self._create_vat_book_line(
            move, line_type)
        # Create tax lines
        ml_taxes = move.line_ids.mapped('tax_ids')
        for tax in ml_taxes.filtered(lambda x: x.id in taxes.ids):
            # Create tax lines for the current vat_book_line
            self._create_vat_book_line_tax(
                tax, line, move)

    def _calculate_vat_book(self):
        """
            This function calculate all the taxes, from issued invoices,
            received invoices and rectification invoices
        """
        for rec in self:
            if not rec.company_id.partner_id.vat:
                raise UserError(
                    _("This company doesn't have VAT"))

            # clean the old records
            rec._clear_old_data()

            tax_model = self.env['account.tax']
            # Obtain Map code template from vat_book.
            tax_code_map = self.env['l10n.es.aeat.map.tax'].search(
                [('model', '=', '340'),
                 '|',
                 ('date_from', '<=', rec.date_start),
                 ('date_from', '=', False),
                 '|',
                 ('date_to', '>=', rec.date_end),
                 ('date_to', '=', False)], limit=1)
            if not tax_code_map:
                raise UserError(_('No AEAT Tax Mapping was found'))

            # Obtain all the codes from account.tax.code.template
            codes_issued = tax_code_map.map_line_ids.mapped(
                'tax_ids').filtered(
                lambda t: t.type_tax_use == 'sale').mapped('description')
            codes_received = tax_code_map.map_line_ids.mapped(
                'tax_ids').filtered(
                lambda t: t.type_tax_use == 'purchase').mapped('description')
            # search the account.tax referred to by the template
            taxes_issued = tax_model.search(
                [('description', 'in', codes_issued),
                 ('company_id', 'child_of', rec.company_id.id)])
            taxes_received = tax_model.search(
                [('description', 'in', codes_received),
                 ('company_id', 'child_of', rec.company_id.id)])

            # Get all the account move lines that contain VAT that is
            #  applicable to this report.
            moves_issued = rec._get_account_moves(taxes_issued)

            for move in moves_issued:
                line_type = 'issued'
                rec._create_vat_book_records(move, line_type, taxes_issued)

            moves_received = rec._get_account_moves(taxes_received)

            for move in moves_received:
                line_type = 'received'
                rec._create_vat_book_records(move, line_type, taxes_received)

            # Issued
            book_type = 'issued'
            issued_tax_lines = rec.issued_line_ids.mapped(
                'tax_line_ids')
            rectification_issued_tax_lines = \
                rec.rectification_issued_line_ids.mapped(
                    'tax_line_ids')
            tax_summary_data_recs = rec._prepare_vat_book_tax_summary(
                issued_tax_lines + rectification_issued_tax_lines, book_type)
            rec._create_vat_book_tax_summary(
                tax_summary_data_recs, rec.issued_tax_summary_ids)
            rec._create_vat_book_summary(rec.issued_tax_summary_ids, book_type)

            # Received
            book_type = 'received'
            received_tax_lines = rec.received_line_ids.mapped(
                'tax_line_ids')
            rectification_received_tax_lines = \
                rec.rectification_received_line_ids.mapped(
                    'tax_line_ids')
            tax_summary_data_recs = rec._prepare_vat_book_tax_summary(
                received_tax_lines + rectification_received_tax_lines,
                book_type)
            rec._create_vat_book_tax_summary(
                tax_summary_data_recs, rec.received_tax_summary_ids)
            rec._create_vat_book_summary(rec.received_tax_summary_ids,
                                         book_type)

            # If we require to auto-renumber invoices received
            if rec.auto_renumber:
                rec_invs = self.env['l10n.es.vat.book.line'].search(
                    [('vat_book_id', '=', rec.id),
                     ('line_type', '=', 'received')],
                    order='invoice_date asc, ref asc')
                i = 1
                for rec_inv in rec_invs:
                    rec_inv.entry_number = i
                    i += 1
                rec_invs = self.env['l10n.es.vat.book.line'].search(
                    [('vat_book_id', '=', rec.id),
                     ('line_type', '=', 'rectification_received')],
                    order='invoice_date asc, ref asc')
                i = 1
                for rec_inv in rec_invs:
                    rec_inv.entry_number = i
                    i += 1
                # Write state and date in the report
            rec.write({
                'state': 'calculated',
                'calculation_date': fields.Datetime.now(),
            })

    @api.multi
    def view_issued_invoices(self):
        self.ensure_one()
        action = self.env.ref(
            'l10n_es_vat_book.action_report_vat_book_invoices_issued')
        vals = action.read()[0]
        vals['context'] = self.env.context
        return vals

    @api.multi
    def view_received_invoices(self):
        self.ensure_one()
        action = self.env.ref(
            'l10n_es_vat_book.action_report_vat_book_invoices_received')
        vals = action.read()[0]
        vals['context'] = self.env.context
        return vals

    def _format_date(self, date):
        # format date following user language
        lang_model = self.env['res.lang']
        lang = lang_model._lang_get(self.env.user.lang)
        date_format = lang.date_format
        return datetime.datetime.strftime(
            fields.Date.from_string(date), date_format)

    @api.multi
    def export_xlsx(self):
        self.ensure_one()
        context = dict(self.env.context, active_ids=self.ids)
        return {
            'name': 'VAT book XLSX report',
            'model': 'l10n.es.vat.book',
            'type': 'ir.actions.report.xml',
            'report_name': 'l10n_es_vat_book.l10n_es_vat_book_xlsx',
            'report_type': 'xlsx',
            'report_file': 'l10n.es.vat.book',
            'context': context,
        }
