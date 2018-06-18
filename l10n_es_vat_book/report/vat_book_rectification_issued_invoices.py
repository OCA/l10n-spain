# -*- coding: utf-8 -*-

from openerp import models
from openerp.report import report_sxw


class VatBookRectificationIssuedInvoicesReport(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(VatBookRectificationIssuedInvoicesReport, self).__init__(
            cr, uid, name, context)


class WrappedVatBookRectificationIssuedInvoices(models.AbstractModel):
    _name = 'report.l10n_es_vat_book.'\
        'tmp_report_vat_book_rectification_issued_invoices'
    _inherit = 'report.abstract_report'
    _template = 'l10n_es_vat_book.'\
        'tmp_report_vat_book_rectification_issued_invoices'
    _wrapped_report_class = VatBookRectificationIssuedInvoicesReport
