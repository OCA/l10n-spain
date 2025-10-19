# Copyright 2023 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.load_data(
        env.cr,
        "l10n_es_aeat_mod347",
        "migrations/15.0.1.6.1/noupdate_changes.xml",
    )
    openupgrade.delete_record_translations(
        env.cr,
        "l10n_es_aeat_mod347",
        ["email_template_347"],
    )
