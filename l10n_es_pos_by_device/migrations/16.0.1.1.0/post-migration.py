def migrate(cr, version):
    if not version:
        return
    cr.execute(
        """
        UPDATE pos_config
        SET pos_sequence_by_device = res_company.pos_sequence_by_device_legacy
        FROM res_company
        WHERE pos_config.company_id = res_company.id;
    """
    )
    cr.execute(
        """
        ALTER TABLE res_company DROP COLUMN pos_sequence_by_device_legacy;
    """
    )
