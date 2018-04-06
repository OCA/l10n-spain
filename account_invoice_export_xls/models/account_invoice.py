# -*- coding: utf-8 -*-
# © 2016 FactorLibre - Hugo Santos <hugo.santos@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _report_xls_fields(self, cr, uid, context=None):
        return [
            'date_invoice', 'move_date', 'invoice_number', 'partner_name',
            'partner_vat', 'amount_untaxed', 'amount_total', 'tax_line_base',
            'tax_line_description', 'tax_line_amount', 'tax_line_base_amount',
            'tax_line_base_tax_code', 'tax_line_base_tax_name',
            'tax_line_tax_amount', 'tax_line_tax_tax_code',
            'tax_line_tax_tax_name'
        ]

    def _report_xls_template(self, cr, uid, context=None):
        return {}
