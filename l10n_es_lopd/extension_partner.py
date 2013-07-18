# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 LambdaSoftware (<http://www.lambdasoftware.net>).
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

from osv import fields, osv

class partner_extension(osv.osv):
	_inherit = 'res.partner'
	_name = 'res.partner'
	_columns = {
		#'name' :fields.char('Nombre o razón social', size=140)
		'actividad':fields.many2one('lopd.actividades','Actividad principal'),
		'encargado':fields.boolean('Encargado de tratamiento', help="Marque esta casilla si es un encargado de tratamiento"),
		'id_fichero':fields.many2many('lopd.fichero','lopd_rel_pafi', 'id_pa', 'id_fi', 'Ficheros'),
	}
	_defaults = {
		'encargado':lambda *a: False,	
	}

partner_extension()


class partner_address_extension(osv.osv):
	_inherit = 'res.partner.address'
	_name = 'res.partner.address'
	_columns = {
		'street': fields.char('Dirección', size=128, help='Dirección'),
        'street2': fields.char('Extra', size=128, help='Use este campo en caso de necesitar más espacio para la dirección'),
	}

partner_address_extension()
