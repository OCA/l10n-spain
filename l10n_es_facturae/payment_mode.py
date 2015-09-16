# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2015 Comunitea Servicios Tecnológicos
#    Omar Castiñeira Saavedra <omar@comunitea.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the Affero GNU General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the Affero GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields


class PaymentModeFaceCode(models.Model):

    _name = "payment.mode.face.code"

    code = fields.Char("Code", size=2, required=True)
    name = fields.Char("Name", required=True)


class PaymentMode(models.Model):

    _inherit = "payment.mode"

    face_code_id = fields.Many2one("payment.mode.face.code", "FACe code")
