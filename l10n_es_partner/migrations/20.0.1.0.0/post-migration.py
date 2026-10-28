# Copyright 2026 Studio73 - Pablo Cortés <pablo.cortes@studio73.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from psycopg2 import sql

_logger = logging.getLogger(__name__)
_SNAPSHOT_BANKS = "l10n_es_partner_pre20_res_bank"
_SNAPSHOT_XMLIDS = "l10n_es_partner_pre20_res_bank_xmlids"
_SNAPSHOT_ACCOUNTS = "l10n_es_partner_pre20_bank_accounts"
_SNAPSHOT_TABLES = (_SNAPSHOT_BANKS, _SNAPSHOT_XMLIDS, _SNAPSHOT_ACCOUNTS)
_COLUMN_QUERIES = {
    _SNAPSHOT_BANKS: "SELECT * FROM public.l10n_es_partner_pre20_res_bank LIMIT 0",
    "l10n_es_bank": "SELECT * FROM public.l10n_es_bank LIMIT 0",
}
_COUNT_QUERIES = {
    _SNAPSHOT_BANKS: "SELECT COUNT(*) FROM public.l10n_es_partner_pre20_res_bank",
    _SNAPSHOT_XMLIDS: (
        "SELECT COUNT(*) FROM public.l10n_es_partner_pre20_res_bank_xmlids"
    ),
    _SNAPSHOT_ACCOUNTS: (
        "SELECT COUNT(*) FROM public.l10n_es_partner_pre20_bank_accounts"
    ),
}

# Old res.bank field names mapped to the standalone catalog model in Odoo 20.
_BANK_FIELD_MAP = {
    "name": "name",
    "lname": "lname",
    "code": "code",
    "bic": "bic",
    "street": "street",
    "street2": "street2",
    "zip": "zip",
    "city": "city",
    "state": "state_id",
    "country": "country_id",
    "email": "email",
    "phone": "phone",
    "active": "active",
    "vat": "vat",
    "website": "website",
    "create_uid": "create_uid",
    "create_date": "create_date",
    "write_uid": "write_uid",
    "write_date": "write_date",
}


def _table_exists(cr, table_name):
    cr.execute("SELECT to_regclass(%s)", (f"public.{table_name}",))
    return bool(cr.fetchone()[0])


def _columns(cr, table_name):
    cr.execute(_COLUMN_QUERIES[table_name])
    return {column.name for column in cr.description}


def _count(cr, table_name):
    cr.execute(_COUNT_QUERIES[table_name])
    return cr.fetchone()[0]


def _restore_banks(cr):
    source_columns = _columns(cr, _SNAPSHOT_BANKS)
    target_columns = _columns(cr, "l10n_es_bank")
    unmapped_columns = sorted(
        source_columns - set(_BANK_FIELD_MAP) - target_columns - {"id"}
    )
    if unmapped_columns:
        raise RuntimeError(
            "The old res_bank table has fields without a l10n.es.bank mapping: "
            + ", ".join(unmapped_columns)
            + ". Keep the migration snapshot and add an explicit field mapping."
        )

    field_pairs = [
        (old_name, new_name)
        for old_name, new_name in _BANK_FIELD_MAP.items()
        if old_name in source_columns and new_name in target_columns
    ]
    field_pairs.extend(
        (column, column)
        for column in sorted((source_columns & target_columns) - set(_BANK_FIELD_MAP))
        if column != "id"
    )
    if not any(new_name == "name" for _old_name, new_name in field_pairs):
        raise RuntimeError("The old res_bank snapshot has no restorable name field")

    target_names = ["id", *(new_name for _old_name, new_name in field_pairs)]
    source_names = ["id", *(old_name for old_name, _new_name in field_pairs)]
    assignments = sql.SQL(", ").join(
        sql.SQL("{} = EXCLUDED.{}").format(
            sql.Identifier(new_name), sql.Identifier(new_name)
        )
        for _old_name, new_name in field_pairs
        if new_name != "id"
    )
    cr.execute(
        sql.SQL(
            "INSERT INTO public.l10n_es_bank ({target_names}) "
            "SELECT {source_names} "
            "FROM public.l10n_es_partner_pre20_res_bank "
            "ON CONFLICT (id) DO UPDATE SET {assignments}"
        ).format(
            target_names=sql.SQL(", ").join(
                sql.Identifier(field_name) for field_name in target_names
            ),
            source_names=sql.SQL(", ").join(
                sql.Identifier(field_name) for field_name in source_names
            ),
            assignments=assignments,
        )
    )

    cr.execute(
        """
        SELECT setval(
            pg_get_serial_sequence('l10n_es_bank', 'id'),
            COALESCE(MAX(id), 1),
            MAX(id) IS NOT NULL
        )
        FROM l10n_es_bank
        """
    )


def _restore_xmlids(cr):
    cr.execute(
        """
        INSERT INTO public.ir_model_data
            (module, name, model, res_id, noupdate)
        SELECT module, name, 'l10n.es.bank', res_id, noupdate
        FROM public.l10n_es_partner_pre20_res_bank_xmlids
        WHERE model = 'res.bank'
        ON CONFLICT (module, name) DO UPDATE SET
            model = EXCLUDED.model,
            res_id = EXCLUDED.res_id,
            noupdate = EXCLUDED.noupdate
        """
    )


def _restore_account_links(cr):
    cr.execute(
        """
        UPDATE public.res_partner_bank AS account
        SET l10n_es_bank_id = snapshot.bank_id
        FROM public.l10n_es_partner_pre20_bank_accounts AS snapshot
        JOIN public.l10n_es_bank AS bank ON bank.id = snapshot.bank_id
        WHERE account.id = snapshot.id
        """
    )
    cr.execute(
        """
        UPDATE public.res_partner_bank AS account
        SET bank_name = COALESCE(NULLIF(account.bank_name, ''), bank.name),
            bank_bic = COALESCE(NULLIF(account.bank_bic, ''), NULLIF(bank.bic, '')),
            street = COALESCE(NULLIF(account.street, ''), NULLIF(bank.street, '')),
            street2 = COALESCE(NULLIF(account.street2, ''), NULLIF(bank.street2, '')),
            zip = COALESCE(NULLIF(account.zip, ''), NULLIF(bank.zip, '')),
            city = COALESCE(NULLIF(account.city, ''), NULLIF(bank.city, '')),
            state_id = COALESCE(account.state_id, bank.state_id),
            country_id = COALESCE(account.country_id, bank.country_id)
        FROM public.l10n_es_bank AS bank
        WHERE account.l10n_es_bank_id = bank.id
        """
    )


def _verify_restoration(cr):
    source_bank_count = _count(cr, _SNAPSHOT_BANKS)
    cr.execute(
        """
        SELECT COUNT(*) FROM public.l10n_es_partner_pre20_res_bank AS source
        JOIN public.l10n_es_bank AS target ON target.id = source.id
        """
    )
    restored_bank_count = cr.fetchone()[0]
    if restored_bank_count != source_bank_count:
        raise RuntimeError(
            f"Restored {restored_bank_count} of {source_bank_count} Spanish banks"
        )

    cr.execute(
        """
        SELECT COUNT(*) FROM public.l10n_es_partner_pre20_res_bank_xmlids AS source
        JOIN public.ir_model_data AS target
          ON target.module = source.module AND target.name = source.name
        WHERE source.model = 'res.bank'
          AND target.model = 'l10n.es.bank'
          AND target.res_id = source.res_id
        """
    )
    restored_xmlid_count = cr.fetchone()[0]
    expected_xmlid_count = _count(cr, _SNAPSHOT_XMLIDS)
    if restored_xmlid_count != expected_xmlid_count:
        raise RuntimeError(
            f"Restored {restored_xmlid_count} of {expected_xmlid_count} bank XML IDs"
        )

    cr.execute(
        """
        SELECT COUNT(*) FROM public.l10n_es_partner_pre20_bank_accounts AS source
        JOIN public.res_partner_bank AS account ON account.id = source.id
        JOIN public.l10n_es_bank AS bank ON bank.id = source.bank_id
        WHERE account.l10n_es_bank_id = source.bank_id
        """
    )
    restored_link_count = cr.fetchone()[0]
    expected_link_count = _count(cr, _SNAPSHOT_ACCOUNTS)
    if restored_link_count != expected_link_count:
        raise RuntimeError(
            "Restored "
            f"{restored_link_count} of {expected_link_count} bank account links"
        )


def migrate(cr, version):
    """Restore the snapshot created before the Odoo 20 base update."""
    existing = [_table_exists(cr, table_name) for table_name in _SNAPSHOT_TABLES]
    if not any(existing):
        if version:
            raise RuntimeError(
                "The installed l10n_es_partner module is being upgraded without "
                "a pre-upgrade bank snapshot. Run the pre-migration script with "
                "--pre-upgrade-scripts before Odoo 20 loads base; do not continue "
                "until the old bank catalog, XML IDs, and account links are backed up."
            )
        _logger.info("No Spanish bank migration snapshot found; nothing to restore")
        return
    if not all(existing):
        raise RuntimeError(
            "Incomplete l10n_es_partner migration snapshot. Keep all remaining "
            "tables and restore the missing snapshot data before continuing."
        )

    _restore_banks(cr)
    _restore_xmlids(cr)
    _restore_account_links(cr)
    _verify_restoration(cr)
    for table_name in _SNAPSHOT_TABLES:
        cr.execute(sql.SQL("DROP TABLE public.{}").format(sql.Identifier(table_name)))
    _logger.info("Restored and verified the Spanish bank catalog and account links")
