# -*- coding: utf-8 -*-
# Copyright 2011 NaN Projectes de Programari Lliure, S.L.
# Copyright 2014 Ángel Moya (Domatix)
# Copyright 2014 Roberto Lizana (Trey)
# Copyright 2013-2016 Pedro M. Baeza

from openerp import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    number = fields.Char(related=False, size=32, copy=False)
    invoice_number = fields.Char(copy=False)

    @api.multi
    def action_move_create(self):
        for inv in self:
            if not inv.invoice_number:
                sequence = inv.journal_id.invoice_sequence_id
                if inv.type in {'out_refund', 'in_refund'}:
                    sequence = inv.journal_id.refund_inv_sequence_id
                if sequence:
                    sequence = sequence.with_context(
                        ir_sequence_date=inv.date or inv.date_invoice)
                    number = sequence.next_by_id()
                else:  # pragma: no cover
                    # Other localizations or not configured journals
                    number = inv.move_id.name
                inv.write({
                    'number': number,
                    'invoice_number': number,
                })
            else:  # pragma: no cover
                inv.number = inv.invoice_number
        res = super(AccountInvoice, self).action_move_create()
        for inv in self:
            # Include the invoice reference on the created journal item
            # This is done for displaying the number on the conciliation
            inv.move_id.ref = (
                "{0} - {1}" if inv.move_id.ref else "{1}"
            ).format(inv.move_id.ref, inv.invoice_number)
        return res

    @api.multi
    def unlink(self):
        """Allow to remove invoices."""
        self.filtered(lambda x: x.journal_id.invoice_sequence_id).write(
            {'move_name': False})
        return super(AccountInvoice, self).unlink()
