# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.tools.sql import column_exists


def migrate(cr, version):
    """The bank account of the declaration is the one of l10n_es_aeat."""
    if not column_exists(cr, "l10n_es_atc_mod420_report", "bank_account_id"):
        return
    cr.execute(
        """
        UPDATE l10n_es_atc_mod420_report SET partner_bank_id = bank_account_id
        WHERE bank_account_id IS NOT NULL AND partner_bank_id IS NULL
        """
    )
