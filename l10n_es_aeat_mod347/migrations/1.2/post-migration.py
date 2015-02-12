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
from openerp.tools import SUPERUSER_ID

def migrate(cr, version):
    cr.execute(
        """UPDATE account_period SET quarter = (
            CASE WHEN (Extract(MONTH from date_start) < 4) THEN 'first'
            WHEN (Extract(MONTH from date_start) < 7) THEN 'second'
            WHEN (Extract(MONTH from date_start) < 10) THEN 'third'
            ELSE 'fourth'
            END)
        WHERE quarter IS NULL""")
