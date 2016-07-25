# -*- coding: utf-8 -*-
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from openerp import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def _invoice_match(env, invoice):
    inv_type = 'out_invoice' if invoice.type == 'out_refund' else 'in_invoice'
    return env['account.invoice'].search([
        ('type', '=', inv_type),
        ('number', '=ilike', invoice.origin),
    ])


def post_init_hook(cr, registry):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        # Linking all refund invoices to its original invoices
        refunds = env['account.invoice'].search([
            ('type', 'in', ('out_refund', 'in_refund')),
        ])
        _logger.info(
            "Linking %d refund invoices", len(refunds))
        for refund in refunds:
            original = _invoice_match(env, refund)
            if original:
                refund.write({
                    'origin_invoice_ids': [(6, 0, original.ids)],
                    'refund_reason': 'Auto',
                })
                idx = 0
                for line in original:
                    refund.invoice_line_ids[idx].write({
                        'origin_line_ids': [(6, 0, line.ids)],
                    })
