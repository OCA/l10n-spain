# -*- coding: utf-8 -*-
# Copyright 2004-2011 Pexego Sistemas Informáticos. (http://pexego.es)
# Copyright 2014-2017 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    refund_invoices_description = fields.Text('Refund invoices description')
    origin_invoices_ids = fields.Many2many(
        comodel_name='account.invoice', column1='refund_invoice_id',
        column2='original_invoice_id', relation='account_invoice_refunds_rel',
        string='Refund invoice', help='Links to original invoice which is '
                                      'referred by current refund invoice',
    )

    @api.model
    def _prepare_refund(self, invoice, date=None, period_id=None,
                        description=None, journal_id=None):
        res = super(AccountInvoice, self)._prepare_refund(
            invoice, date=date, period_id=period_id,
            description=description, journal_id=journal_id,
        )
        res['origin_invoices_ids'] = [(6, 0, invoice.ids)]
        res['refund_invoices_description'] = description
        return res
