# Copyright 2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_move am
        SET sii_description = COALESCE(ai.sii_manual_description, ai.sii_description),
            sii_state = ai.sii_state,
            sii_csv = ai.sii_csv,
            sii_return = ai.sii_return,
            sii_header_sent = ai.sii_header_sent,
            sii_content_sent = ai.sii_content_sent,
            sii_send_error = ai.sii_send_error,
            sii_send_failed = ai.sii_send_failed,
            sii_refund_type = ai.sii_refund_type,
            sii_refund_specific_invoice_type = ai.sii_refund_specific_invoice_type,
            sii_account_registration_date = ai.sii_account_registration_date,
            sii_registration_key = ai.sii_registration_key,
            sii_registration_key_additional1 = ai.sii_registration_key_additional1,
            sii_registration_key_additional2 = ai.sii_registration_key_additional2,
            sii_property_location = ai.sii_property_location,
            sii_property_cadastrial_code = ai.sii_property_cadastrial_code
        FROM account_invoice ai
        WHERE ai.id = am.old_invoice_id""",
    )
    openupgrade.logged_query(
        env.cr,
        """
        INSERT INTO account_move_queue_job_rel
        (invoice_id, job_id)
        SELECT am.id, rel.job_id
        FROM account_invoice_queue_job_rel rel
        JOIN account_move am ON am.old_invoice_id = rel.invoice_id
        """,
    )
    # Change jobs reference
    pattern = r"account\.invoice\((.*),\)\.(confirm_one_invoice|cancel_one_invoice)\(\)"
    pattern2 = r"(.*)\"model\": \"account.invoice\"(.*)\"ids\": \[(.*)\](.*)"
    openupgrade.logged_query(
        env.cr,
        r"""
        WITH sub AS (
            SELECT id, regexp_matches(func_string, $$%(pattern)s$$) as parts,
                regexp_matches(records, $$%(pattern2)s$$) as parts2
            FROM queue_job
            WHERE func_string ~ $$%(pattern)s$$
        )
        UPDATE queue_job qj
        SET func_string = concat('account.move(', am.id::text, ',).', parts[2], '()'),
            model_name = 'account.move',
            name = concat('account.move.', method_name),
            channel_method_name = concat('<account.move>.', parts[2]),
            records = concat(
                sub.parts2[1], '"model": "account.move"', sub.parts2[2],
                '"ids": [', am.id, ']', sub.parts2[4]
            )
        FROM sub
        JOIN account_move am ON am.old_invoice_id = sub.parts[1]::int
        WHERE sub.id = qj.id"""
        % {"pattern": pattern, "pattern2": pattern2},
    )
    openupgrade.load_data(
        env.cr, "l10n_es_aeat_sii_oca", "migrations/13.0.1.0.0/noupdate_changes.xml"
    )
