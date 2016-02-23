# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP - Account banking sepa bank suffix
#    Copyright (C) 2016 Comunitea Servicios Tecnológicos.
#    Omar Castiñeira Saavedra - omar@comunitea.com
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

from openerp import models, fields, api, exceptions, _


class PaymentMode(models.Model):

    _inherit = "payment.mode"

    suffix = fields.Char("Suffix", size=3, help='Suffix for sepa identifiers '
                                                'with this payment mode. If '
                                                'not set it will use the '
                                                'company configuration.')

    @api.one
    @api.constrains('suffix')
    def _check_suffix_format(self):
        if self.suffix:
            if len(self.suffix) != 3 or not self.suffix.isdigit():
                raise exceptions.\
                    Warning(_("Suffix must be compound by 3 numbers"))
