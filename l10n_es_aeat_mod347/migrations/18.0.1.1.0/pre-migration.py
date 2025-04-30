# Copyright 2025 Moduon Team S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from openupgradelib import openupgrade


def migrate(cr, version):
    openupgrade.rename_columns(
        cr, {"res_partner": [("not_in_mod347", "old_not_in_mod347")]}
    )
