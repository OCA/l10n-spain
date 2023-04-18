# Copyright 2011 NaN Projectes de Programari Lliure, S.L.
# Copyright 2014 Ángel Moya (Domatix)
# Copyright 2014 Roberto Lizana (Trey)
# Copyright 2013-2016 Pedro M. Baeza

from odoo import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    number = fields.Char(related=False, size=32, copy=False)
    invoice_number = fields.Char(copy=False)

    def _get_seq_number_next_stuff(self):
        self.ensure_one()
        chart = self.company_id.chart_template_id
        journal_sequence, domain = super(
            AccountInvoice, self,
        )._get_seq_number_next_stuff()
        if chart in chart._get_spanish_charts():
            if self.type in ['in_refund', 'out_refund']:
                journal_sequence = self.journal_id.refund_inv_sequence_id
            else:
                journal_sequence = self.journal_id.invoice_sequence_id
        return journal_sequence, domain

    @api.multi
    def action_move_create(self):
        res = super(AccountInvoice, self).action_move_create()
        for inv in self:
            if not inv.invoice_number:
                sequence = inv.journal_id.invoice_sequence_id
                if inv.type in {'out_refund', 'in_refund'} and \
                        inv.journal_id.refund_inv_sequence_id:
                    sequence = inv.journal_id.refund_inv_sequence_id
                if sequence:
                    sequence = sequence.with_context(
                        ir_sequence_date=inv.date or inv.date_invoice,
                        ir_sequence_date_range=inv.date or inv.date_invoice,
                    )
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
        return res

    def invoice_validate(self):
        """Include the invoice reference on the created journal item.
        This is done for displaying the number on the conciliation.
        It needs to be done here after a patch on core.
        """
        res = super().invoice_validate()
        for inv in self:
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
