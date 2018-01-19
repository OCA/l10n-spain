# -*- coding: utf-8 -*-
# Copyright 2017 Eficent Business & IT Consult. Services <contact@eficent.com>
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging
from odoo import SUPERUSER_ID
from odoo.api import Environment

logger = logging.getLogger(__name__)


def update_account_move_line(cr, op_key_taxes):
    for op_key_tax in op_key_taxes:
        aeat_349_operation_key = op_key_tax.l10n_es_aeat_349_operation_key
        cr.execute("""
            UPDATE account_move_line aml
            SET l10n_es_aeat_349_operation_key = %s
            FROM account_move_line_account_tax_rel AS rel
            WHERE rel.account_tax_id = %s and aml.id = rel.account_move_line_id
        """, (aeat_349_operation_key, op_key_tax.id))
        logger.info('Updated account move lines for operation key %s and tax '
                    '%s' % (aeat_349_operation_key, op_key_tax.name))


def post_init_hook(cr, registry):
    env = Environment(cr, SUPERUSER_ID, {})
    taxes = env['account.tax'].search([])
    op_key_taxes = taxes.filtered(lambda x: x.l10n_es_aeat_349_operation_key)
    update_account_move_line(cr, op_key_taxes)
