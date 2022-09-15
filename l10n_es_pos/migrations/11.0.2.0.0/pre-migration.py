# Copyright 2018 David Vidal <david.vidal@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from psycopg2 import sql


def migrate(cr, version):
    if not version:
        return
    # Add new column in advance
    cr.execute("""
        ALTER TABLE pos_order
        ADD COLUMN is_l10n_es_simplified_invoice BOOLEAN;
    """)
    # If migrated directly from 10.0.1.0.0
    simplified_invoice_field = 'simplified_invoice'
    cr.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name='pos_order' AND column_name='simplified_invoice';
    """)
    # Otherwise it's migrated from 11.0.1.0.0
    if not cr.fetchone():
        simplified_invoice_field = 'l10n_es_simplified_invoice_number'
    # Move simplified invoice info to pos_reference field.
    cr.execute(
        sql.SQL(
            """UPDATE pos_order SET
            pos_reference = %(s)s, is_l10n_es_simplified_invoice = TRUE
            WHERE COALESCE({}, '') != ''"""
        ).format(sql.Identifier(simplified_invoice_field))
    )
