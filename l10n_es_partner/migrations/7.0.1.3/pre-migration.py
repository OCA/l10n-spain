# -*- coding: utf-8 -*-
##############################################################################
#
# OpenERP, Open Source Management Solution
# Copyright (c) 2015 Incaser (http://www.incaser.es)
# Sergio Teruel <sergio@incaser.es>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
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
from psycopg2 import IntegrityError
__name__ = ("Cambia identificadores de los bancos por nueva nomenclatura")


def clear_identifiers(cr):
    sql = ("SELECT id, res_id FROM ir_model_data "
           "WHERE model='res.bank' AND module='l10n_es_partner'")
    cr.execute(sql)
    for row in cr.fetchall():
        sql = ("UPDATE ir_model_data "
               "SET name='res_bank_es_' || (SELECT code "
               "                            FROM res_bank "
               "                            WHERE id=%s) "
               "WHERE id=%s" % (row[1], row[0]))
        try:
            cr.execute(sql)
            cr.commit()
        except IntegrityError:
            # XML-ID duplicado - Intentar eliminar
            cr.rollback()
            try:
                cr.execute("DELETE FROM res_bank WHERE id=%s" % row[1])
                cr.execute("DELETE FROM ir_model_data WHERE id=%s" % row[0])
                cr.commit()
            except IntegrityError:
                # No se puede eliminar por dependencias - Ignorar error
                cr.rollback()


def migrate(cr, version):
    if not version:
        return
    clear_identifiers(cr)
