# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2011
#        Pexego Sistemas Informáticos. (http://pexego.es) All Rights Reserved
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

__author__ = "Luis Manuel Angueira Blanco (Pexego)"


from osv import osv, fields


class account_fiscal_position(osv.osv):
    """
    Inheritance of Account fiscal position to add field 'include_in_mod349'.
    This fields let us map fiscal position, taxes and accounts to create an AEAT 349 Report
    """
    _inherit = 'account.fiscal.position'

    _columns = {
        'intracommunity_operations' : fields.boolean('Intra-Community operations'),
    }

account_fiscal_position()