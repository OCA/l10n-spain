# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2013 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                       Pedro Manuel Baeza <pedro.baeza@serviciosbaeza.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
__name__ = ("Rename some columns and convert sequence field")

def migrate_templates(cr, version):
    # Rename report_id to template_id on templates lines
    cr.execute("""ALTER TABLE account_balance_reporting_template_line
                  RENAME COLUMN report_id to template_id""")
    # Add temporary column to template lines
    cr.execute("""ALTER TABLE account_balance_reporting_template_line
                  ADD COLUMN sequence_temp integer""")
    # Change sequence number to template lines
    cr.execute("""SELECT id, template_id, sequence
                  FROM account_balance_reporting_template_line
                  ORDER BY template_id, sequence""")
    ant_template = -1
    sequence = 1
    for record in cr.fetchall():
        if record[1] != ant_template:
            sequence = 1
            ant_template = record[1]
        cr.execute("""UPDATE account_balance_reporting_template_line
                      SET sequence_temp=%s
                      WHERE id=%s""", (sequence, record[0]))
        sequence += 1
    # Remove old column and change the name to the new one
    cr.execute("""ALTER TABLE account_balance_reporting_template_line
                  DROP COLUMN sequence""")
    cr.execute("""ALTER TABLE account_balance_reporting_template_line
                  RENAME COLUMN sequence_temp to sequence""")

def migrate_reports(cr, version):
    # Add temporary column to report lines
    cr.execute("""ALTER TABLE account_balance_reporting_line
                  ADD COLUMN sequence_temp integer""")
    # Change sequence number to report lines
    cr.execute("""SELECT id, report_id, sequence
                  FROM account_balance_reporting_line
                  ORDER BY report_id, sequence""")
    ant_report = -1
    sequence = 1
    for record in cr.fetchall():
        if record[1] != ant_report:
            sequence = 1
            ant_report = record[1]
        cr.execute("""UPDATE account_balance_reporting_line
                      SET sequence_temp=%s
                      WHERE id=%s""", (sequence, record[0]))
        sequence += 1
    # Remove old column and change the name to the new one
    cr.execute("""ALTER TABLE account_balance_reporting_line
                  DROP COLUMN sequence""")
    cr.execute("""ALTER TABLE account_balance_reporting_line
                  RENAME COLUMN sequence_temp to sequence""")

def migrate(cr, version):
    migrate_templates(cr, version)
    migrate_reports(cr, version)