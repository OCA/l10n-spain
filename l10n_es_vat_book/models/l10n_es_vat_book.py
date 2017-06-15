# -*- coding: utf-8 -*-
from openerp import models, api, fields, _
from openerp.exceptions import Warning


class L10nEsVatBook(models.Model):
    _inherit = "l10n.es.aeat.report"
    _name = 'l10n.es.vat.book'
    _period_quarterly = False
    _period_monthly = True
    _period_yearly = True

    number = fields.Char(
        default=_("vat_book"))

    issued_invoice_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.issued.lines',
        inverse_name='l10n_es_vat_book_id',
        string=_('Issued invoices'))

    received_invoice_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.received.lines',
        inverse_name='l10n_es_vat_book_id',
        string=_('Received received'))

    rectification_invoice_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.rectification.lines',
        inverse_name='l10n_es_vat_book_id',
        string=_('Rectification received'))

    amount_without_tax_issued = fields.Float(
        string=_('Total without taxes'))

    amount_tax_issued = fields.Float(
        string=_('Taxes'))

    amount_total_issued = fields.Float(
        string=_('Total'))

    issued_tax_summary = fields.One2many(
        comodel_name='l10n.es.vat.book.issued.tax.summary',
        inverse_name='vat_book_id',
        string=_("Issued tax summary"))

    amount_without_tax_received = fields.Float(
        string=_('Total without taxes'))

    amount_tax_received = fields.Float(
        string=_('Taxes'))

    amount_total_received = fields.Float(
        string=_('Total'))

    received_tax_summary = fields.One2many(
        comodel_name='l10n.es.vat.book.received.tax.summary',
        inverse_name='vat_book_id',
        string=_("Received tax summary"))

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            fy = self.env['account.fiscalyear'].browse(
                vals['fiscalyear_id'])[0]
            period = vals['period_type']
            if vals['period_type'] == '0A':
                period = '00'

            vals['name'] = _('vat_book') + "_" + fy.name + period + self.\
                _report_identifier_get(vals)
        return super(L10nEsVatBook, self).create(vals)

    @api.multi
    def button_calculate(self):
        """
            Funcion call from vat_book
        """
        self._calculate_vat_book()
        return True

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
        new_record = False
        invoice_vals = self._get_vals_invoice_line()

        if invoice_id.type in ('out_invoice'):
            new_record = issued_invoice_obj.create(invoice_vals)
        elif invoice_id.type in ('in_invoice'):
            new_record = received_invoice_obj.create(invoice_vals)
        # TODO Facturas rectificativas
        # elif invoice_id.type in ('out_refund'):
        #     tax_ven_rect.append(i)
        # elif invoice_id.type in ('in_refund'):
        #     tax_comp_rect.append(i)
        return new_record

    def _calculate_vat_book(self):
        """
            This function calculate all the taxes, from issued invoices,
            received invoices and rectification invoices
        """
        invoice_obj = self.env['account.invoice']
        tax_code_obj = self.env['account.tax.code']
        if not self.company_id.partner_id.vat:
            raise Warning(
                _("This company doesn't have NIF"))

        # clean the old invoice records
        self.issued_invoice_ids.unlink()
        self.received_invoice_ids.unlink()
        self.rectification_invoice_ids.unlink()

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
            if invoice_tax_code_ids not in tax_code_ids.ids:
                continue

            invoice_vat_book_line_id = \
                self._create_new_invoice_line(invoice_id)

            # TODO Recorrer los impuestos

        # Write state and date in the report
        # self.write({
        #     'state': 'calculated',
        #     # 'calculation_date': fields.Datetime.now(),
        # })


    def __init__(self, pool, cr):
        self._aeat_number = 'vat_book'
        super(L10nEsVatBook, self).__init__(pool, cr)
