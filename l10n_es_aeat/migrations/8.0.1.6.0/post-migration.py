# -*- coding: utf-8 -*-
# © 2016 Antiun Ingenieria S.L. - Antonio Espinosa
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
from openerp import SUPERUSER_ID
from openerp.api import Environment


def migrate(cr, version):
    if not version:
        return
    cr.execute(
        """SELECT count(attname) FROM pg_attribute WHERE attrelid =
        ( SELECT oid FROM pg_class WHERE relname = 'l10n_es_aeat_tax_line' )
        AND attname = 'legacy_report_id'"""
    )
    if not cr.fetchone():
        return
    env = Environment(cr, SUPERUSER_ID, {})
    sequences = env['ir.sequence'].search([
        ('code', '=', 'aeat.sequence.type'),
    ])
    for seq in sequences:
        seq.prefix = re.sub(r'-', '', seq.prefix)
        seq.padding = 13 - len(seq.prefix)

    cr.execute(
        """
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_schema='public' AND
              table_name like 'l10n_es_aeat_%_report';
        """)
    for table_schema, table_name in cr.fetchall():
        cr.execute(
            """
            ALTER TABLE %(table)s
            DROP CONSTRAINT IF EXISTS %(table)s_sequence_uniq;
            """ % {'table': table_name})
