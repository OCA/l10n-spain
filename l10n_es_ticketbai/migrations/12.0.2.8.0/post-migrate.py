# Copyright 2022 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


def migrate(cr, version):
    if not version or not openupgrade.table_exists(cr, 'account_fp_tbai_tax'):
        return

    cr.execute(
        """
        DROP TABLE account_fp_tbai_tax;
        """
    )