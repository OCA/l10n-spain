# Copyright 2018 David Vidal <david.vidal@tecnativa.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from openupgradelib import openupgrade
from odoo.addons.l10n_es_pos.hooks import post_init_hook


@openupgrade.migrate()
def migrate(env, version):
    pos_config = env['pos.config'].search([])
    vals = {}
    for pos in pos_config:
        vals[pos] = {
            'padding': pos.simple_invoice_prefix,
            'prefix': pos.simple_invoice_prefix,
            'number_next_actual': pos.simple_invoice_number,
        }
    post_init_hook(env.cr, False, vals)
