# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2015 Omar Castiñeira Savedra (http://www.pexego.es)
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


class ResPartner(models.Model):

    _inherit = "res.partner"

    facturae = fields.Boolean('Factura electrónica')
    organo_gestor = fields.Char('Órgano gestor', size=10)
    unidad_tramitadora = fields.Char('Unidad tramitadora', size=10)
    oficina_contable = fields.Char('Oficina contable', size=10)
    organo_proponente = fields.Char('Órgano proponente', size=10)
