# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2011 Ting. All Rights Reserved
#    Copyright (c) 2011-2013 Acysos S.L.(http://acysos.com) All Rights Reserved
#                       Ignacio Ibeas Izquierdo <ignacio@acysos.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
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

from openerp.osv import orm


def migrate(cr, version):
    if not version:
        return

    cr.execute(
        "UPDATE account_invoice_tax itax "
        "SET tax_id = subq.tax_id "
        "FROM (SELECT t.id as tax_id, itax2.id as itax_id "
        "    FROM account_tax t "
        "    JOIN account_invoice_tax itax2 ON t.company_id = t.company_id "
        "    WHERE t.name IN (select unnest(regexp_split_to_array(itax2.name, E' - '))::varchar) "
        "    OR t.description IN (select unnest(regexp_split_to_array(itax2.name, E' - '))::varchar) "
        ") AS subq "
        "WHERE itax.id = subq.itax_id")
    cr.execute("SELECT COUNT(*) FROM account_invoice_tax WHERE tax_id IS NULL")
    res = cr.fetchall()
    print res
    if res[0][0]:
        raise orm.except_orm('Error', 'Unable to retrieve the source tax for some invoice tax lines')
    