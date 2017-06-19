#-*- coding:utf-8 -*-

from openerp.osv import osv
from openerp.report import report_sxw


class vat_book_rectification_received_invoices_report(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(vat_book_rectification_received_invoices_report, self).__init__(
            cr, uid, name, context)


class wrapped_vat_book_rectification_received_invoices(osv.AbstractModel):
    _name = 'report.l10n_es_vat_book.'\
        'tmp_report_vat_book_rectification_received_invoices'
    _inherit = 'report.abstract_report'
    _template = 'l10n_es_vat_book.'\
        'tmp_report_vat_book_rectification_received_invoices'
    _wrapped_report_class = vat_book_rectification_received_invoices_report
