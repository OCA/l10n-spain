# -*- encoding: utf-8 -*-
# Copyright 2017 Tecnativa - Pedro M. Baeza

from osv import osv, fields

import logging

_logger = logging.getLogger(__name__)


class account_invoice_refund(osv.osv_memory):
    _inherit = "account.invoice.refund"


    def _default_sii_refund_type_required(self, cr, uid, context=None):
        active_id = context and context.get('active_id', False)
        if active_id:
            invoice = self.pool.get('account.invoice').browse(cr, uid, active_id, context=context)
            return invoice.company_id.sii_enabled

        return False

    _sii_refund_type = [('S', 'By substitution'),('I', 'By differences')]

    _columns = {
        'sii_refund_type_required': fields.boolean('Is SII Refund Type required?'),
        'sii_refund_type': fields.selection(_sii_refund_type, 'SII Refund Type'),
    }

    _defaults = {
        'sii_refund_type_required': _default_sii_refund_type_required,
    }


    def compute_refund(self, cr, uid, ids, mode='refund', context=None):
        inv_obj = self.pool.get('account.invoice')

        if context is None:
            context = {}

        result = super(account_invoice_refund, self).compute_refund(cr, uid, ids, mode, context)

        created_inv = [x[2] for x in result['domain'] if x[0] == 'id']
        if context.get('active_ids') and created_inv and created_inv[0]:
            for form in self.read(cr, uid, ids, context=context):
                refund_inv_id = created_inv[0][0]
                inv_obj.write(cr, uid, [refund_inv_id], {
                    'sii_refund_type': form['sii_refund_type'] or False
                })

        return result
