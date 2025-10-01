# Copyright 2025 Moduon - Emilio Pascual
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def migrate(cr, version):
    """Fix account_move without `prorate_id` and account_move_line without computed
    `with_vat_prorate` after the special prorate update."""
    # Update prorate_id in account_move
    cr.execute(
        """
        UPDATE account_move am
        SET prorate_id = (
            SELECT rcvp.id
            FROM res_company_vat_prorate rcvp
            WHERE rcvp.company_id = am.company_id
            AND rcvp.date <= COALESCE(
                am.date,
                am.invoice_date,
                CURRENT_DATE
            )
            ORDER BY rcvp.date DESC
            LIMIT 1
        )
        FROM res_company rc
        WHERE am.company_id = rc.id
        AND rc.with_vat_prorate = true
        AND am.prorate_id IS NULL
        """
    )
    # Update with_vat_prorate in account_move_line
    cr.execute(
        """
        UPDATE account_move_line aml
        SET with_vat_prorate = rc.with_vat_prorate = true
                AND (rcvp.type = 'general' OR rcvp.special_vat_prorate_default = true)
        FROM account_move am
        INNER JOIN res_company rc ON am.company_id = rc.id
        LEFT JOIN res_company_vat_prorate rcvp ON am.prorate_id = rcvp.id
        WHERE aml.move_id = am.id
        AND aml.with_vat_prorate IS NOT TRUE
        """
    )
