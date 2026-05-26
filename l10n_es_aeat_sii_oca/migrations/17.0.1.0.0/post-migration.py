# Copyright 2025 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_move am
        SET sii_send_date = job.eta,
            sii_needs_cancel = CASE
                WHEN job.func_string LIKE '%cancel_one_invoice()' THEN True
            ELSE
                False
            END
        FROM account_move_queue_job_rel rel
        JOIN queue_job job ON job.id = rel.job_id
        WHERE rel.invoice_id = am.id
            AND job.state = 'pending' AND job.eta IS NOT NULL
        """,
    )
    openupgrade.logged_query(
        env.cr, "DELETE FROM queue_job WHERE channel = 'root.invoice_validate_sii'"
    )
    openupgrade.logged_query(
        env.cr,
        "DELETE FROM queue_job_function WHERE channel_id = %s",
        (env.ref("l10n_es_aeat_sii_oca.invoice_validate_sii").id,),
    )
