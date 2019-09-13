# Copyright 2019 Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.load_data(
        env.cr, 'payment_redsys', 'migrations/11.0.1.0.0/noupdate_changes.xml')
