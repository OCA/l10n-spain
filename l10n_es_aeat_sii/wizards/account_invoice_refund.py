# -*- coding: utf-8 -*-
# Copyright 2017 Tecnativa - Pedro M. Baeza

from openerp.osv import osv, fields


class AccountInvoiceRefund(osv.TransientModel):
    _inherit = "account.invoice.refund"

    def _default_sii_refund_type_required(self, cr, uid, context):
        if context.get('active_ids'):
            invoices = self.pool['account.invoice'].browse(cr, uid, context.get('active_ids'), context)
            for inv in invoices:
                if inv.sii_enabled:
                    return True
        return False


    _columns = {
        'sii_refund_type_required': fields.boolean(string="Is SII Refund Type required?", ),
        'sii_refund_type': fields.selection(selection=[('S', 'By substitution'), ('I', 'By differences')], string="SII Refund Type")

    }

    _defaults = {
        'sii_refund_type_required': _default_sii_refund_type_required,
    }

    def compute_refund(self, cr, uid, ids, mode='refund', context=None):

        inv_obj = self.pool.get('account.invoice')

        if context is None:
            context = {}

        result = super(AccountInvoiceRefund, self).compute_refund(cr, uid, ids, mode, context)

        created_inv = [x[2] for x in result['domain'] if x[0] == 'id' and x[1] == 'in']
        if context.get('active_ids') and created_inv and created_inv[0]:
            for form in self.browse(cr, uid, ids, context=context):
                if form.sii_refund_type:
                    refund_inv_id = created_inv[0][0]
                    inv_obj.write(cr, uid, [refund_inv_id], {
                        'sii_refund_type': form.sii_refund_type,
                    })
        return result