# -*- coding: utf-8 -*-
# Copyright 2017 Tecnativa - Pedro M. Baeza

from openerp.osv import osv, fields


class AccountInvoiceRefund(osv.TransientModel):
    _inherit = "account.invoice.refund"

    def _default_sii_refund_type_required(self, cr, uid, ids, context):
        invoices = self.env['account.invoice'].browse(cr, uid, context.get('active_ids'), context)
        return any(invoices.mapped('company_id.sii_enabled'))


    _columns = {
        'sii_refund_type_required': fields.boolean(string="Is SII Refund Type required?", ),
        'sii_refund_type': fields.selection(selection=[('S', 'By substitution'), ('I', 'By differences')], string="SII Refund Type")

    }

    _defaults = {
        'sii_refund_type_required': _default_sii_refund_type_required,
    }
