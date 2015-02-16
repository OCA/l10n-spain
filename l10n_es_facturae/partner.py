# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2015 Omar Castiñeira Savedra (http://www.pexego.es)
#    Copyright (c) 2015 Factor Libre (http://www.factorlibre.com)
#                       Ismael Calvo <ismael.calvo@factorlibre.com)
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

from osv import osv, fields


class res_partner_address(osv.osv):

    _inherit = "res.partner.address"

    _columns = {
        'facturae': fields.boolean('Factura electrónica'),
        'organo_gestor': fields.char(size=100, string='Órgano gestor'),
        'unidad_tramitadora': fields.char(size=100,
                                          string='Unidad tramitadora'),
        'oficina_contable': fields.char(size=100, string='Oficina contable'),
    }

res_partner_address()
