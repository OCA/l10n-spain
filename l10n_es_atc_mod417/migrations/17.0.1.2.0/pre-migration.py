# Copyright 2026 Tecnativa - Carlos Lopez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def migrate(cr, version):
    # Remove old attachment to force re-download of the new version of the ATC jar
    cr.execute("DELETE FROM ir_attachment WHERE name = 'pa-mod417.jar';")
