# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Serv. Tecnol. Avanz. (<http://www.serviciosbaeza.com>)
#                       Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
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


def rename_fiscal_positions(cr):
    cr.execute("""
        UPDATE account_fiscal_position
        SET name='Régimen Extracomunitario / Canarias, Ceuta y Melilla'
        WHERE name='Régimen Extracomunitario'
        """)


def migrate(cr, version):
    if not version:
        return
    rename_fiscal_positions(cr)
