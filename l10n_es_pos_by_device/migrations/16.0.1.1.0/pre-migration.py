def migrate(cr, version):
    if not version:
        return

    cr.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name='res_company' AND column_name='pos_sequence_by_device'
    """
    )
    column_exists = cr.fetchone()

    if column_exists:
        cr.execute(
            """
            ALTER TABLE res_company
            RENAME COLUMN pos_sequence_by_device TO
            pos_sequence_by_device_legacy
        """
        )
