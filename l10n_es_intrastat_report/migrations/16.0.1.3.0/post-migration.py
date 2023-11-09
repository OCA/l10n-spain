# Copyright 2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade, openupgrade_merge_records

_xmlids_merge_records = [
    (
        "l10n_es_intrastat_report.intrastat_transaction_11",
        "intrastat_product.intrastat_transaction_11",
    ),
    (
        "l10n_es_intrastat_report.intrastat_transaction_12",
        "intrastat_product.intrastat_transaction_12",
    ),
    (
        "l10n_es_intrastat_report.intrastat_transaction_21",
        "intrastat_product.intrastat_transaction_21",
    ),
    (
        "l10n_es_intrastat_report.intrastat_transaction_22",
        "intrastat_product.intrastat_transaction_22",
    ),
    (
        "l10n_es_intrastat_report.intrastat_transaction_23",
        "intrastat_product.intrastat_transaction_23",
    ),
    (
        "l10n_es_intrastat_report.intrastat_transaction_31",
        "intrastat_product.intrastat_transaction_31",
    ),
    (
        "l10n_es_intrastat_report.intrastat_transaction_32",
        "intrastat_product.intrastat_transaction_32",
    ),
    (
        "l10n_es_intrastat_report.intrastat_transaction_33",
        "intrastat_product.intrastat_transaction_33",
    ),
    (
        "l10n_es_intrastat_report.intrastat_transaction_34",
        "intrastat_product.intrastat_transaction_34",
    ),
    (
        "l10n_es_intrastat_report.intrastat_transaction_41",
        "intrastat_product.intrastat_transaction_41",
    ),
    (
        "l10n_es_intrastat_report.intrastat_transaction_42",
        "intrastat_product.intrastat_transaction_42",
    ),
    (
        "l10n_es_intrastat_report.intrastat_transaction_51",
        "intrastat_product.intrastat_transaction_51",
    ),
    (
        "l10n_es_intrastat_report.intrastat_transaction_52",
        "intrastat_product.intrastat_transaction_52",
    ),
    (
        "l10n_es_intrastat_report.intrastat_transaction_71",
        "intrastat_product.intrastat_transaction_71",
    ),
    (
        "l10n_es_intrastat_report.intrastat_transaction_72",
        "intrastat_product.intrastat_transaction_72",
    ),
    (
        "l10n_es_intrastat_report.intrastat_transaction_80",
        "intrastat_product.intrastat_transaction_80",
    ),
    (
        "l10n_es_intrastat_report.intrastat_transaction_91",
        "intrastat_product.intrastat_transaction_91",
    ),
    (
        "l10n_es_intrastat_report.intrastat_transaction_99",
        "intrastat_product.intrastat_transaction_99",
    ),
]


@openupgrade.migrate()
def migrate(env, version):
    """Merge records from intrastat.transaction.
    Existing records from l10n_en_intrastat_report will be merged into
    intrastat_product records.
    Remove obsolote transactions (previously archived)."""
    for item in _xmlids_merge_records:
        old_record = env.ref(item[0], raise_if_not_found=False)
        new_record = env.ref(item[1], raise_if_not_found=False)
        if old_record and new_record:
            openupgrade_merge_records.merge_records(
                env=env,
                model_name="intrastat.transaction",
                record_ids=old_record.ids,
                target_record_id=new_record.id,
                method="sql",
            )
