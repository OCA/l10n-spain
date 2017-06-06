# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2017 MINORISA (http://www.minorisa.net) All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    sii_exempt_cause = fields.Selection(
        string="Exempt Cause",
        selection=[('none', 'None'),
                   ('E1', 'E1'),
                   ('E2', 'E2'),
                   ('E3', 'E3'),
                   ('E4', 'E4'),
                   ('E5', 'E5'),
                   ('E6', 'E6')],
        default='none')
