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

"""
Extends the account journals to add fields used by the 347 report.
"""

from osv import osv, fields

class res_partner(osv.osv):
    """
    Extends the partners to add the include_in_mod347 field
    """
    _inherit = "res.partner"
    
    _columns = {
        'include_in_mod347' : fields.boolean(u"Include in 347 Report",
            help="Include in AEAT 347 Model report"),
    }

    _defaults = {
        'include_in_mod347' : lambda *a: True,
    }

res_partner()