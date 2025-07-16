# Copyright 2025 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.l10n_es_vat_prorate.hooks import pre_init_hook  # pylint: disable=W8150


def migrate(cr, version):
    pre_init_hook(cr)
