# Copyright 2022 Acsone SA - Xavier Bouquiaux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade

from odoo.addons.l10n_es_aeat.hooks import create_column_thirdparty_invoice


@openupgrade.migrate()
def migrate(env, version):
    create_column_thirdparty_invoice(env.cr)
