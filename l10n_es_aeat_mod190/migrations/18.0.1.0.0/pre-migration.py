from openupgradelib import openupgrade

_renamed_xmlids = [
    (
        "l10n_es_aeat_mod190.aeat_mod190_main_export_line_8",
        "l10n_es_aeat_mod190.aeat_mod190_main_export_line_08",
    ),
    (
        "l10n_es_aeat_mod190.aeat_mod190_main_export_line_9",
        "l10n_es_aeat_mod190.aeat_mod190_main_export_line_09",
    ),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_xmlids(env.cr, _renamed_xmlids)
