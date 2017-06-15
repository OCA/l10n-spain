# -*- coding: utf-8 -*-
from openerp import models, api, fields, _


class L10nEsVatBookReceivedTaxSummary(models.Model):
    _inherit = 'l10n.es.vat.book.issued.tax.summary'
    _name = 'l10n.es.vat.book.received.tax.summary'
