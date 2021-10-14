# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_move am
        SET correction_method = ai.correction_method,
            facturae_refund_reason = ai.facturae_refund_reason,
            facturae_start_date = ai.facturae_start_date,
            facturae_end_date = ai.facturae_end_date
        FROM account_invoice ai
        WHERE ai.id = am.old_invoice_id""",
    )

    if openupgrade.column_exists(env.cr, "account_invoice", "integration_issue"):
        openupgrade.logged_query(
            env.cr,
            """
            UPDATE account_move am
            SET integration_issue = ai.integration_issue
            FROM account_invoice ai
            WHERE ai.id = am.old_invoice_id""",
        )

    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_move_line aml
        SET facturae_receiver_contract_reference =
                ail.facturae_receiver_contract_reference,
            facturae_receiver_contract_date =
                ail.facturae_receiver_contract_date,
            facturae_receiver_transaction_reference =
                ail.facturae_receiver_transaction_reference,
            facturae_receiver_transaction_date = ail.facturae_receiver_transaction_date,
            facturae_issuer_contract_reference = ail.facturae_issuer_contract_reference,
            facturae_issuer_contract_date = ail.facturae_issuer_contract_date,
            facturae_issuer_transaction_reference =
                ail.facturae_issuer_transaction_reference,
            facturae_issuer_transaction_date = ail.facturae_issuer_transaction_date,
            facturae_file_reference = ail.facturae_file_reference,
            facturae_file_date = ail.facturae_file_date,
            facturae_start_date = ail.facturae_start_date,
            facturae_end_date = ail.facturae_end_date,
            facturae_transaction_date = ail.facturae_transaction_date
        FROM account_invoice_line ail
        WHERE ail.id = aml.old_invoice_line_id
            AND (
                ail.facturae_receiver_contract_reference is not NULL
                OR ail.facturae_receiver_contract_date is not NULL
                OR ail.facturae_receiver_transaction_reference is not NULL
                OR ail.facturae_receiver_transaction_date is not NULL
                OR ail.facturae_issuer_contract_reference is not NULL
                OR ail.facturae_issuer_contract_date is not NULL
                OR ail.facturae_issuer_transaction_reference is not NULL
                OR ail.facturae_issuer_transaction_date is not NULL
                OR ail.facturae_file_reference is not NULL
                OR ail.facturae_file_date is not NULL
                OR ail.facturae_start_date is not NULL
                OR ail.facturae_end_date is not NULL
                OR ail.facturae_transaction_date is not NULL
            )
        """,
    )
