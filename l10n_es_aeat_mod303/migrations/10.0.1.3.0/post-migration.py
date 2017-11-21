# -*- coding: utf-8 -*-
# Copyright 2014-2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def migrate(cr, version):
    if not version:
        return
    # for not requiring openupgradelib if not migrating
    from openupgradelib import openupgrade
    openupgrade.logged_query(
        cr, """
        UPDATE l10n_es_aeat_mod303_report
        SET result_type = 'C'
        WHERE %s = True""" % openupgrade.get_legacy_name('compensate')
    )
