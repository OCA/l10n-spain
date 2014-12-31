# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2014 Domatix (http://www.domatix.com)
#                       Angel Moya <angel.moya@domatix.com>
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

from openerp import models, api


class AccountTax(models.Model):
    _inherit = 'account.tax'

    @api.multi
    def name_get(self):
        result = []
        for tax in self:
            result.append((tax.id, tax.name))
        return result
