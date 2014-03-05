# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Spanish Localization Team
#    $Id$
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

from openerp.osv import orm, fields


class ResPartner(orm.Model):
    _inherit = 'res.partner'

    _columns = {
        'es_libro': fields.char('Book', size=128),  # libro
        # Registro Mercantil
        'es_registro_mercantil': fields.char('Commercial Registry', size=128),
        'es_hoja': fields.char('Sheet', size=128),  # hoja
        'es_folio': fields.char('Page', size=128),  # folio
        'es_seccion': fields.char('Section', size=128),  # seccion
        'es_tomo': fields.char('Volume', size=128),  # tomo
    }
