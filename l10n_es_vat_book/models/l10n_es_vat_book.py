# -*- coding: utf-8 -*-
from openerp import models, api, fields, _


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
        print "Entro en el boton calculate"
        import ipdb; ipdb.set_trace()
        return True

    def __init__(self, pool, cr):
        self._aeat_number = 'vat_book'
        super(L10nEsVatBook, self).__init__(pool, cr)
