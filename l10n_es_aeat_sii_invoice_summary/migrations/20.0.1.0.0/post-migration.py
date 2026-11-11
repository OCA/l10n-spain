# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """The summary type is now the invoice type: F4 for a range, F2 for a
    single simplified invoice and R5 for a summary of credit notes. The
    summaries already sent keep the type the AEAT holds, which the
    `l10n_es_aeat_sii_oca` migration has set."""
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_move
           SET l10n_es_invoice_type = CASE
                   WHEN move_type = 'out_refund' THEN 'R5'
                   WHEN sii_invoice_summary_start IS NOT NULL
                        AND sii_invoice_summary_start
                            IS DISTINCT FROM sii_invoice_summary_end
                       THEN 'F4'
                   ELSE 'F2'
               END
         WHERE is_invoice_summary
           AND move_type IN ('out_invoice', 'out_refund')
           AND aeat_content_sent IS NULL
           AND l10n_es_invoice_type IS NOT NULL
        """,
    )
