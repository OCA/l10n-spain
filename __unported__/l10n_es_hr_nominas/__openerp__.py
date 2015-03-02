# -*- encoding: utf-8 -*-
##############################################################################
#
#    AvanzOSC, Avanzed Open Source Consulting
#    Copyright (C) 2009 Ting! (<http://www.ting.es>). All Rights Reserved
#    Copyright (c) 2010 Acysos S.L. (http://acysos.com) All Rights Reserved.
#                       Update to OpenERP 6.0 Ignacio Ibeas <ignacio@acysos.com> 
#    Copyright (C) 2011-2012 Iker Coranti (www.avanzosc.com). All Rights Reserved
#                       Update to OpenERP 6.1 Iker Coranti
#    
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
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################
{
    "name": "Recursos Humanos: Gestión de Nóminas",
    "version": "1.0",
    "depends": ["base",
                "hr",
                "account",
                ],
    "author": "Ting!, Acysos S.L., AvanzOSC,Odoo Community Association (OCA)",
    "category": "Generic Modules/Human Resources",
    "description": """
                Recursos Humanos: Gestión de Nóminas
                Este módulo permite automatizar la creación de los asientos contables para las nóminas de los empleados.
        
                Uso del módulo:
                    - El primer paso es configurar las cuentas y el diario en el que se van a contabilizar las nóminas para ello hay que ir a Administración / Usuarios / Árbol de la compañía / Compañías y dentro de la página configuración de compañías configurar estas cuentas.
                    - Se deben poner los datos de la nómina en la ficha del empleado en recursos humanos dentro de la pestaña salario
                    - Para generar las nóminas se usa el asistente definido dentro de Recursos Humanos / Nóminas y anticipos / Asistentes / Generar Nóminas
                    - Para ver las nóminas se debe ir al menú Recursos Humanos / Nóminas y anticipos /  Nóminas / Todas las Nóminas
                    - Existen asistentes para crear anticipos y pagas extras, así como para confirmar y pagar las nóminas de todos los empleados seleccionados y para confirmar y pagar los anticipos
                    - Para ver los anticipos se debe ir al menú Recursos Humanos / Nóminas y anticipos / Anticipos / Todos los anticipos
    """,
    "init_xml": [],
    'update_xml': [
                 'hr_nominas_view.xml',
                 'wizard/wizard_crea_nominas_view.xml',
                 'wizard/wizard_pagar_anticipos_view.xml',
                 'wizard/wizard_pagar_nominas_view.xml',  
                  ],
    'demo_xml': [],
    'installable': False,
    'active': False,
}
