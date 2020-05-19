# -*- coding: utf-8 -*-
##############################################################################
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


class ResPartner(orm.Model):
    _inherit = "res.partner"
    _columns = {
        'not_in_mod347': fields.boolean(
            "Not included in 347 report",
            help="If you mark this field, this partner will not be included "
            "in any AEAT 347 model report, independently from the total "
            "amount of its operations."),
    }

    _defaults = {
        'not_in_mod347': False,
    }
