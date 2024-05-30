# Copyright 2024 Dixmit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def pre_init_hook(cr):
    """Precreate Information, as it could take a long time and recompute work if done by ORM"""
    cr.execute("ALTER TABLE account_move ADD COLUMN IF NOT EXISTS payment_date DATE")
    cr.execute(
        "ALTER TABLE account_move ADD COLUMN IF NOT EXISTS payment_ratio_create FLOAT"
    )
    cr.execute(
        "ALTER TABLE account_move ADD COLUMN IF NOT EXISTS payment_ratio_bill_date FLOAT"
    )
    cr.execute(
        "ALTER TABLE account_move ADD COLUMN IF NOT EXISTS payment_ratio_validation FLOAT"
    )
    cr.execute(
        """
        UPDATE account_move am
        SET payment_date = T.payment_date,
            payment_ratio_create = - T.payment_ratio_create * am.amount_total_signed,
            payment_ratio_bill_date = - T.payment_ratio_bill_date * am.amount_total_signed,
            payment_ratio_validation = - T.payment_ratio_validation * am.amount_total_signed
        FROM (
            SELECT am.id, MAX(am2.date) as payment_date,
                EXTRACT(DAY FROM MAX(am2.date)::timestamp-am.create_date::timestamp)
                    as payment_ratio_create,
                EXTRACT(DAY FROM MAX(am2.date)::timestamp-am.invoice_date::timestamp)
                    as payment_ratio_bill_date,
                EXTRACT(DAY FROM MAX(am2.date)::timestamp-am.date::timestamp)
                    as payment_ratio_validation
            FROM account_move am
            INNER JOIN res_company rc ON rc.id = am.company_id
            INNER JOIN res_currency cur ON cur.id = rc.currency_id
            INNER JOIN account_move_line aml ON aml.move_id = am.id
            INNER JOIN account_partial_reconcile apr
                ON apr.credit_move_id = aml.id OR apr.debit_move_id = aml.id
            INNER JOIN account_move_line aml2
                ON aml2.id!= aml.id
                    AND (apr.credit_move_id = aml2.id OR apr.debit_move_id = aml2.id)
            INNER JOIN account_move am2 ON am2.id = aml2.move_id
            WHERE am.move_type in ('in_refund', 'in_invoice')
                AND abs(am.amount_residual) < cur.rounding
                AND am.state = 'posted'
            GROUP BY am.id
        ) T
        WHERE T.id = am.id
        """
    )
