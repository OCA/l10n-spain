# -*- coding: utf-8 -*-
# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def migrate(cr, version):
    if not version:
        return
    cr.execute("""
        UPDATE l10n_es_aeat_mod303_report
        SET cuota_compensar = abs(cuota_compensar)""")
