# -*- coding: utf-8 -*-
# © 2016 Ainara Galdona <ainaragaldona@avanzosc.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def migrate_method_time(cr, version):

    cr.execute("""UPDATE account_asset_category
                  SET method_time = ext_method_time""")
    cr.execute("""UPDATE account_asset_asset
                  SET method_time = ext_method_time""")


def migrate(cr, version):
    if not version:
        return
    migrate_method_time(cr, version)
