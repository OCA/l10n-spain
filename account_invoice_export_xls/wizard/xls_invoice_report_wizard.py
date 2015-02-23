# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp.osv import orm, fields


class XlsInvoiceReportWizard(orm.TransientModel):
    _name = 'xls.invoice.report.wizard'

    INVOICE_TYPES = [
        ('out_invoice', 'Customer Invoice'),
        ('out_refund', 'Customer Refund Invoice'),
        ('in_invoice', 'Supplier Invoice'),
        ('in_refund', 'Supplier Refund Invoice')
    ]

    _columns = {
        'period_id': fields.many2one('account.period', 'Period'),
        'invoice_type': fields.selection(INVOICE_TYPES, 'Invoice Type',
                                         required=True),
        'period_ids': fields.many2many(
            'account.period', 'period_xls_invoice_report_rel',
            'wizard_id', 'period_id', 'Periods'),
        'company_id': fields.many2one('res.company', 'Company',
                                      required=True)
    }

    _defaults = {
        'company_id': lambda self, cr, uid, context: self.pool['res.users']
        .browse(cr, uid, [uid], context)[0].company_id.id
    }

    def xls_export(self, cr, uid, ids, context=None):
        wiz = self.browse(cr, uid, ids[0], context=context)
        datas = {
            'model': 'xls.invoice.report.wizard',
            'invoice_type': wiz.invoice_type,
            'company_id': wiz.company_id.id,
            'period_ids': map(lambda p: p.id, wiz.period_ids),
            'ids': [wiz.id]
        }

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'account.invoice.export.xls',
            'datas': datas
        }
