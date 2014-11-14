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

##########################################################################
# Copias de seguridad
##########################################################################


class lopd_copia_seguridad(osv.osv):
    _name = 'lopd.copia.seguridad'
    _descripcion = 'Copias de seguridad'
    _columns = {
        'id_soporte': fields.many2one('lopd.soportes', 'Soportes', required=True),
        'fecha': fields.date('Fecha de la copia', required=True),
        'periodicidad': fields.selection([('1', 'Copia diaria'), ('7', '1 vez a la semana'), ('30', '1 vez al mes')], 'Periodicidad', required=True),
        'recuperacion': fields.selection([('1', 'Sí'), ('2', 'No'), ], '¿Existen procedimientos de recuperación de datos?', required=True),
    }
    _defaults = {
        'fecha': lambda *a: time.strftime("%Y-%m-%d"),
        'periodicidad': 'sem',
        'recuperacion': '2',
    }
lopd_copia_seguridad()

##########################################################################
# Registro de incidencias
##########################################################################


class lopd_incidencias(osv.osv):
    _name = 'lopd.incidencias'
    _description = 'Registro de incidencias'
    _columns = {
        'id': fields.integer('Número de incidencia', required=True, readonly=True),
        'f_notificacion': fields.datetime('Fecha de notificación', help='Fecha y hora en la que se notifica la incidencia'),
        'f_incidencia': fields.datetime('Fecha de la incidencia', help='Fecha y hora en la que se produjo la incidencia'),
        'tipo': fields.char('Tipo de incidencia', size=64, required=True),
        'descripcion': fields.text('Descripción', size=250, required=True),
        'notificada_por': fields.char('Persona que notifica', size=64, required=True),
        'notificada_a': fields.char('A quién se notifica', size=64, required=True),
        'autorizacion': fields.selection([('1', 'Sí'), ('2', 'No'), ], 'Autorización', required=True),
        'efectos': fields.char('Efectos que puede producir', size=64, required=True),
        'ejecuta': fields.char('Quién ejecuta el proceso', size=64, required=True),
        'datos_rest': fields.char('Datos restaurados', size=64, required=True),
        'datos_manu': fields.char('Datos grabados manualmente', size=64, required=True),

    }
    _defaults = {
        'f_notificacion': lambda *a: time.strftime("%Y-%m-%d %H:%M:%S"),
        # 'f_incidencia' : lambda *a : time.strftime("%Y-%m-%d %H:%M:%S"),
        'autorizacion': '2',
    }

lopd_incidencias()

##########################################################################
# Entradas/Salidas de soportes
##########################################################################


class lopd_io_soporte(osv.osv):
    _name = 'lopd.io.soporte'
    _description = 'Registro de salidas de soportes'
    _columns = {
        'fecha': fields.datetime('Fecha de salida y hora', required=True),
        'fecha_devolucion': fields.date('Fecha de devolución', required=True),
        'id_soporte': fields.many2many('lopd.soportes', 'lopd_rel_iosop', 'id_io', 'id_so', 'Soportes', required=True),
        # Finalidad de la salida / Forma de envío
        'io_detalle': fields.text('IO_Finalidad_Forma', size=250, required=True),
        # id_empleado: Receptor en caso de entrada Emisor en caso de salida
        'id_empleado': fields.many2one('hr.employee', 'Usuario', required=True),
        # nombre: Emisor en caso de entrada, destinatario en caso de salida
        'nombre': fields.char('Dombre', size=64, required=True),
        'autorizacion': fields.selection([('1', 'Sí'), ('2', 'No'), ], 'Autorización', required=True),
        'observaciones': fields.text('Observaciones', size=250),
        # Entrada / Salida (0 = salida, 1 = Entrada)
        'io_mode': fields.boolean('Entrada/Salida', required=True),
    }
    _defaults = {
        'fecha': lambda *a: time.strftime("%Y-%m-%d %H:%M:%S"),
        'fecha_devolucion': lambda *a: time.strftime("%Y-%m-%d"),
        'autorizacion': '2',
        'io_mode': lambda self, cr, uid, context: context.get('io_mode', None),
    }

lopd_io_soporte()
