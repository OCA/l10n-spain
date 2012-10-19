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

{
	"name" : "LOPD",
	"version" : "1.0.1",
	"category" : "Generic Modules/Protección de datos",
	"description": """
	Módulo de implentación de la Ley Orgánica de Proteccion de Datos en OpenERP.
        Serán necesarias las siguientes dependencias en el sistema (servidor):
            pdftk, PIL, reportlab, suds

    * IMPORTANTE: El sistema está configurado para pruebas, se deben cambiar las líneas 1002 y 1003 del archivo fichero_nota.py
            La primera línea invoca al servicio de pruebas, la segunda invocará al de registros:
            resultado = client.service.probarXml(envio)
            #resultado = client.service.registrarXml(envio)
	""",
	"author" : "LambdaSoftware development team",
	"website" : "http://www.lambdasoftware.net",
	'depends': ['base','hr','l10n_es_toponyms'],
	'init_xml': [
		'data/lopd.sos.tipos.xml',
		'data/lopd.equipos.tipos.xml',
		'data/lopd.recursos.tipos.xml',
		'data/lopd.programas.tipos.xml',
		'data/lopd.soportes.tipos.xml',
		'data/lopd.actividades.xml',
		'data/lopd.categoria.destinatarios.xml',
	],
	'update_xml': [
		'security/permisos_lopd.xml',
        'security/ir.model.access.csv',
		'vistas/vista_lopd.xml',
		'vistas/vista_tipos.xml',
		'vistas/vista_hr.xml',
		'vistas/vista_partner.xml',
		'vistas/vista_registros.xml',
		'vistas/vista_figura_tratamiento.xml',
		'vistas/vista_declarante.xml',
		'vistas/vista_fichero.xml',
		'vistas/vista_solicitudes.xml',
		'vistas/lopd_menus.xml',
		'wizard/lopd_fichero_wizard.xml',
	],
	'demo_xml': [],
	'installable': True,
	'active': False,
}

