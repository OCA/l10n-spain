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
from openerp import fields, models, api


class ResPartner(models.Model):
    _inherit = "res.partner"

    not_in_mod347 = fields.Boolean(
        "Not included in 347 report",
        help="If you mark this field, this partner will not be included in "
             "any AEAT 347 model report, independently from the total "
             "amount of its operations.", default=False)

    @api.model
    def _commercial_fields(self):
        res = super(ResPartner, self)._commercial_fields()
        res += ['not_in_mod347']
        return res
