# -*- coding: utf-8 -*-
# © 2016 FactorLibre - Hugo Santos <hugo.santos@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models


class XlsInvoiceReportWizard(models.TransientModel):
    _name = 'xls.invoice.report.wizard'

    INVOICE_TYPES = [
        ('out_invoice', 'Customer Invoice'),
        ('out_refund', 'Customer Refund Invoice'),
        ('in_invoice', 'Supplier Invoice'),
        ('in_refund', 'Supplier Refund Invoice')
    ]

    period_id = fields.Many2one('account.period', 'Period')
    invoice_type = fields.Selection(INVOICE_TYPES, 'Invoice Type',
                                    required=True)
    period_ids = fields.Many2many('account.period', string='Periods')
    company_id = fields.Many2one(
        'res.company', 'Company', required=True,
        default=lambda self: self.env['res.company']._company_default_get(
            'account.invoice'))

    @api.multi
    def xls_export(self):
        self.ensure_one()
        datas = {
            'model': 'xls.invoice.report.wizard',
            'invoice_type': self.invoice_type,
            'company_id': self.company_id.id,
            'period_ids': map(lambda p: p.id, self.period_ids),
            'ids': [self.id]
        }

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'account.invoice.export.xls',
            'datas': datas
        }
