# -*- coding: utf-8 -*-
# © 2016 - Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def migrate(cr, version):
    if not version:
        return
    cr.execute(
        """SELECT count(attname) FROM pg_attribute WHERE attrelid =
        ( SELECT oid FROM pg_class WHERE relname = 'l10n_es_aeat_tax_line' )
        AND attname = 'legacy_report_id'"""
    )
    if cr.fetchone()[0] != 1:
        return
    cr.execute(
        """
        UPDATE l10n_es_aeat_tax_line
        SET model = 'l10n.es.aeat.mod303.report',
            res_id = legacy_report_id
        WHERE model is NULL
        """)
