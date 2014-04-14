# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C)
#        2004-2011: Pexego Sistemas Informáticos. (http://pexego.es)
#        2013:      Top Consultant Software Creations S.L.
#                   (http://www.topconsultant.es/)
#        2014:      Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                   Pedro M. Baeza <pedro.baeza@serviciosbaeza.com> 
#
#    Autor original: Luis Manuel Angueira Blanco (Pexego)
#    Migración OpenERP 7.0: Ignacio Martínez y Miguel López.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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
from openerp.osv import fields, orm


class account_fiscal_position(orm.Model):
    """
    Inheritance of Account fiscal position to add field 'include_in_mod349'.
    This fields let us map fiscal position, taxes and accounts to create an
    AEAT 349 Report
    """
    _inherit = 'account.fiscal.position'
    _columns = {
        'intracommunity_operations': fields.boolean(
                                                'Intra-Community operations'),
    }
