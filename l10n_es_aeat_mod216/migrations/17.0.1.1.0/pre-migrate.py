# Copyright 2025 Moduon Team S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from openupgradelib import openupgrade

_rename_fields = [
    (
        "l10n.es.aeat.mod216.report",
        "l10n_es_aeat_mod216_report",
        "casilla_01",
        "casilla_01_pre_2024",
    ),
    (
        "l10n.es.aeat.mod216.report",
        "l10n_es_aeat_mod216_report",
        "casilla_03",
        "casilla_03_pre_2024",
    ),
    (
        "l10n.es.aeat.mod216.report",
        "l10n_es_aeat_mod216_report",
        "casilla_04",
        "casilla_04_pre_2024",
    ),
    (
        "l10n.es.aeat.mod216.report",
        "l10n_es_aeat_mod216_report",
        "casilla_05",
        "casilla_05_pre_2024",
    ),
    (
        "l10n.es.aeat.mod216.report",
        "l10n_es_aeat_mod216_report",
        "casilla_06",
        "casilla_06_pre_2024",
    ),
    (
        "l10n.es.aeat.mod216.report",
        "l10n_es_aeat_mod216_report",
        "casilla_07",
        "casilla_07_pre_2024",
    ),
]


@openupgrade.migrate()
def migrate(env, version):
    for model, table, oldfield, newfield in _rename_fields:
        if not openupgrade.column_exists(env.cr, table, oldfield):
            continue
        openupgrade.rename_fields(env, [(model, table, oldfield, newfield)])
