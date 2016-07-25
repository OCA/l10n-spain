# -*- coding: utf-8 -*-
# Copyright 2004-2011 Pexego Sistemas Informáticos. (http://pexego.es)
# Copyright 2014 Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api


class AccountInvoiceRefund(models.TransientModel):
    _inherit = "account.invoice.refund"

    @api.multi
    def compute_refund(self, mode='refund'):
        result = super(AccountInvoiceRefund, self).compute_refund(mode)
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            return result
        # An example of result['domain'] computed by the parent wizard is:
        # [('type', '=', 'out_refund'), ('id', 'in', [43L, 44L])]
        # The created refund invoice is the first invoice in the
        # ('id', 'in', ...) tupla
        created_inv = [x[2] for x in result['domain']
                       if x[0] == 'id' and x[1] == 'in']
        if created_inv and created_inv[0]:
            description = self[0].description or ''
            refund_inv_id = created_inv[0][0]
            refund = self.env['account.invoice'].browse(refund_inv_id)
            refund.write({
                'origin_invoice_ids': [(6, 0, active_ids)],
                'refund_reason': description,
            })
            # Try to match refund invoice lines with original invoice lines
            if len(active_ids) == 1:
                invoice = self.env['account.invoice'].browse(active_ids[0])
                idx = 0
                for line in invoice:
                    refund.invoice_line_ids[idx].write({
                        'origin_line_ids': [(6, 0, line.ids)],
                    })

        return result
