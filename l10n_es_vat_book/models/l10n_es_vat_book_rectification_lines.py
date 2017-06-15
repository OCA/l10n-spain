# -*- coding: utf-8 -*-
from openerp import models, api, fields, _


class L10nEsVatBookRectificationLines(models.Model):
    _inherit = 'l10n.es.vat.book.issued.lines'
    _name = 'l10n.es.vat.book.rectification.lines'
