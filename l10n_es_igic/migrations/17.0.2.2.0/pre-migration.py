from openupgradelib import openupgrade

merged_modules = {"l10n_es_dua_igic": "l10n_es_igic"}


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.update_module_names(env.cr, merged_modules.items(), merge_modules=True)
