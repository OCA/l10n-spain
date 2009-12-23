# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2009 Ting! (<http://www.ting.es>). All Rights Reserved
#    $Id$
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
{
    "name" : "Recursos Humanos: Gestión de Nóminas",
    "version" : "0.9",
    "author" : "Ting!",
    "website": "http://www.ting.es",
    "category" : "Generic Modules/Human Resources",
    "license" : "GPL-3",
    "description": """ Recursos Humanos: Gestión de Nóminas
        Este módulo permite automatizar la creación de los asientos contables para las nóminas de los empleados.
        
        Uso del módulo:
            - El primer paso es configurar las cuentas y el diario en el que se van a contabilizar las nóminas para ello hay que ir a Administración -> Usuarios -> Arbol de la compañia -> Compañias y dentro de la página configuración de compañias configurar estas cuentas.
            - Se deben poner los datos de la nómina en la ficha del empleado en recursos humanos dentro de la pestaña salario
            - Para generar las nóminas se usa el wizard definido dentro de Recursos Humanos -> Nóminas y anticipos -> Asistentes -> Generar Nóminas
            - Para ver las nóminas se debe ir al menú Recursos Humanos -> Nóminas y anticipos ->  Nóminas -> Ver Todas las Nóminas
            - Existen wizards para crear anticipos y pagas extras, así como para confirmar y pagar las nóminas de todos los empleados seleccionados y para pagar los anticipos
            - Para ver los anticipos se debe ir al menú Recursos Humanos -> Nóminas y anticipos -> Anticipos ->Ver los anticipos

""",
    "depends": ['base','hr','account'],
    "init_xml": [],
    "update_xml": ['security/ir.model.access.csv','view_nominas.xml','hr_nominas_wizard.xml','data/hr_nominas.xml'],
    "demo_xml": [],
    "installable": True,
    "active": False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
