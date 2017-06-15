# -*- coding: utf-8 -*-
from openerp import models, api, fields, _


class L10nEsVatBookReceivedLines(models.Model):
    _inherit = 'l10n.es.vat.book.issued.lines'
    _name = 'l10n.es.vat.book.received.lines'

    tax_lines_received_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.invoice.tax.lines',
        inverse_name='received_invoice_line_id',
        string=_("Tax Lines"))
