# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

from odoo.fields import Command

# Supplier refunds were mapped to boxes [70] and [71] besides [88] and [89].
# These lines are no longer in the data files, but deleting them would cascade
# to the tax lines of the declarations already calculated with them, so they
# are kept without taxes: old declarations keep their detail and amounts and
# new ones get nothing there.
OLD_PURCHASE_LINES = [
    "atc_mod425_map_line_70_purchase",
    "atc_mod425_map_line_71_purchase",
]


@openupgrade.migrate()
def migrate(env, version):
    map_lines = env["l10n.es.aeat.map.tax.line"]
    for xmlid in OLD_PURCHASE_LINES:
        map_lines |= (
            env.ref(f"l10n_es_atc_mod425.{xmlid}", raise_if_not_found=False)
            or map_lines.browse()
        )
    if not map_lines:
        return
    openupgrade.set_xml_ids_noupdate_value(
        env, "l10n_es_atc_mod425", OLD_PURCHASE_LINES, True
    )
    map_lines.tax_xmlid_ids = [Command.clear()]
