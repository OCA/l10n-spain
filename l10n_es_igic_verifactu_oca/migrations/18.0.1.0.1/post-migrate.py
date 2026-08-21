# Copyright 2026 Binhex - Mario Montes <m.montes@binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    from odoo.addons.l10n_es_igic_verifactu_oca.hooks import post_init_hook

    post_init_hook(env)
