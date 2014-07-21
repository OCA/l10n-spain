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
import time

class hr_employee(osv.osv):
	_inherit = 'hr.employee'
	_name = 'hr.employee'
	_columns = {
#		'nombre':fields.char('Nombre', size = 35, required = True),
#		'apel1':fields.char('Primer Apellido', size=35, required = True),
#		'apel2':fields.char('Segundo Apellido', size=35),
		'f_alta':fields.date('Fecha alta'),
		'f_baja':fields.date('Fecha baja'),
		'esadmin':fields.boolean('¿Es administrador?'),
		'id_equipo':fields.many2many('lopd.equipos','lopd_rel_usreq','id_usr','id_eq','Equipo'),
		'id_recurso':fields.many2many('lopd.recursos','lopd_rel_usrre','id_usr','id_re','Recursos'),
		'id_programa':fields.many2many('lopd.programas','lopd_rel_usrpr','id_usr','id_pr','Programas'),
	}
	_defaults = {
		'f_alta' : lambda *a : time.strftime("%Y-%m-%d"),
		'f_baja' : lambda *a : time.strftime("%Y-%m-%d"),
		'esadmin': lambda *a: False,
	}

hr_employee()



