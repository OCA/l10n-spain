# -*- coding: utf-8 -*-
# © 2016 - Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def migrate(cr, version):
    if not version:
        return
    cr.execute("SELECT 1 FROM pg_class WHERE relname='l10n_es_aeat_tax_line'")
    if not cr.fetchone():
        return
    cr.execute(
        """
        ALTER TABLE l10n_es_aeat_tax_line
        RENAME report TO legacy_report_id
        """)
