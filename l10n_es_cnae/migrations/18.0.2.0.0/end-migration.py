# Copyright 2026 Moduon Team S.L. <info@moduon.team>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3).
# It's an end script, so it runs after l10n_eu_nace's one.
from odoo import SUPERUSER_ID, api

from odoo.addons.l10n_es_cnae.hooks import migrate_to_cnae2025


def migrate(cr, version):
    migrate_to_cnae2025(api.Environment(cr, SUPERUSER_ID, {}))
