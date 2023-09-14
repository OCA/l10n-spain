# Copyright 2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

_field_renames = [
    (
        "l10n.es.intrastat.product.declaration",
        "l10n_es_intrastat_product_declaration",
        "type",
        "declaration_type",
    ),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_fields(env, _field_renames)
