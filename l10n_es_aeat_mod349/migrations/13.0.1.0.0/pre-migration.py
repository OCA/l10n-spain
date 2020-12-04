# Copyright 2020 ForgeFlow
# Copyright 2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade  # pylint: disable=W7936

field_renames = [
    (
        "l10n.es.aeat.mod349.report",
        "l10n_es_aeat_mod349_report",
        "type",
        "statement_type",
    ),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_fields(env, field_renames)
