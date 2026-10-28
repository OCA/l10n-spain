# Copyright 2026 Studio73 - Pablo Cortés <pablo.cortes@studio73.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)
_SNAPSHOT_BANKS = "l10n_es_partner_pre20_res_bank"
_SNAPSHOT_XMLIDS = "l10n_es_partner_pre20_res_bank_xmlids"
_SNAPSHOT_ACCOUNTS = "l10n_es_partner_pre20_bank_accounts"
_SNAPSHOT_TABLES = (_SNAPSHOT_BANKS, _SNAPSHOT_XMLIDS, _SNAPSHOT_ACCOUNTS)


def _table_exists(cr, table_name):
    cr.execute("SELECT to_regclass(%s)", (f"public.{table_name}",))
    return bool(cr.fetchone()[0])


def _column_exists(cr, table_name, column_name):
    cr.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
              AND column_name = %s
        )
        """,
        (table_name, column_name),
    )
    return cr.fetchone()[0]


def migrate(cr, version):
    """Snapshot Odoo 19 banks before Odoo 20 loads ``base`` and drops them."""
    existing = [_table_exists(cr, table_name) for table_name in _SNAPSHOT_TABLES]
    if all(existing):
        _logger.info("Spanish bank migration snapshot already exists; reusing it")
        return
    if any(existing):
        raise RuntimeError(
            "Incomplete l10n_es_partner migration snapshot. Keep the database "
            "unchanged and inspect the l10n_es_partner_pre20_* tables."
        )

    if not _table_exists(cr, "res_bank"):
        if _table_exists(cr, "ir_module_module"):
            cr.execute(
                """
                SELECT 1 FROM ir_module_module
                WHERE name = 'l10n_es_partner' AND state = 'installed'
                """
            )
            if cr.fetchone():
                raise RuntimeError(
                    "Cannot find res_bank before migrating l10n_es_partner. "
                    "Run this script with --pre-upgrade-scripts before Odoo 20 "
                    "loads base."
                )
        _logger.info("No installed Odoo 19 res.bank catalog to snapshot")
        return

    missing_tables = [
        table_name
        for table_name in ("ir_model_data", "res_partner_bank")
        if not _table_exists(cr, table_name)
    ]
    if missing_tables:
        raise RuntimeError(
            "Cannot snapshot the Spanish bank catalog; missing tables: "
            + ", ".join(missing_tables)
        )

    cr.execute(
        "CREATE TABLE public.l10n_es_partner_pre20_res_bank "
        "AS SELECT * FROM public.res_bank"
    )
    cr.execute(
        """
        CREATE TABLE public.l10n_es_partner_pre20_res_bank_xmlids AS
        SELECT * FROM public.ir_model_data WHERE model = 'res.bank'
        """
    )
    if _column_exists(cr, "res_partner_bank", "bank_id"):
        cr.execute(
            """
            CREATE TABLE public.l10n_es_partner_pre20_bank_accounts AS
            SELECT id, bank_id FROM public.res_partner_bank
            WHERE bank_id IS NOT NULL
            """
        )
    else:
        cr.execute(
            """
            CREATE TABLE public.l10n_es_partner_pre20_bank_accounts (
                id integer NOT NULL,
                bank_id integer NOT NULL
            )
            """
        )

    cr.execute("SELECT COUNT(*) FROM public.l10n_es_partner_pre20_res_bank")
    bank_count = cr.fetchone()[0]
    _logger.info("Snapshotted %s banks and their XML IDs and account links", bank_count)
