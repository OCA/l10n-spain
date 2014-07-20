# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2008 ACYSOS S.L. (http://acysos.com) All Rights Reserved.
#                       Pedro Tarrafeta <pedro@acysos.com>
#    Copyright (c) 2012 Servicios Tecnológicos Avanzados (http://www.serviciosbaeza.com)
#                       Pedro Manuel Baeza <pedro.baeza@serviciosbaeza.com>
#    Copyright (c) 2012 Avanzosc (http://www.avanzosc.com)
#    Copyright (c) 2013 Joaquin Gutierrez (http://www.gutierrezweb.es)
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    2013/09/08 - Joaquín Gutierrez: Adaptación a la versión 7
#    2013/09/09 - Pedro M. Baeza: Refactorización general
#
##############################################################################

{
    'name' : "Cierre de ejercicio fiscal para España",
    'version' : "1.0",
    'author' : "Pexego",
    'website' : "http://www.pexego.es",
    'contributors' : ['Pedro M. Baeza', 'Joaquín Gutierrez'],
    'category' : "Localisation/Accounting",
    'description': """
Cierre contable del ejercicio fiscal español 
============================================
    
Reemplaza el asistente por defecto de OpenERP para el cierre contable (del 
módulo *account*) por un asistente todo en uno más avanzado que permite:

 * Comprobar asientos descuadrados.
 * Comprobar fechas y periodos incorrectos de los apuntes.
 * Comprobar si hay asientos sin asentar en el ejercicio a cerrar.
 * Crear el asiento de pérdidas y ganancias.
 * Crear el asiento de pérdidas y ganancias de patrimonio neto.
 * Crear el asiento de cierre.
 * Crear el asiento de apertura.

Permite configurar todos los parámetros para la realización de los asientos, 
aunque viene preconfigurado para el actual plan de cuentas español. 

Para la creación de los asientos, se tiene en cuenta el método de cierre 
definido en los tipos de cuenta (siempre que la cuenta no sea de tipo view):

 * Ninguno: No se realiza ningún cierre para esa cuenta.
 * Saldo: Crea un apunte para la cuenta con el saldo del ejercicio.
 * No conciliados: Crea un apunte por cada empresa con saldo para la cuenta.
 * Detalle: No soportado.

También conserva el estado del cierre, por lo que el usuario puede cancelar y 
deshacer las operaciones fácilmente.
    """,
    "license" : "AGPL-3",
    "depends" : [
        "base",
        "account",
        "l10n_es",
    ],
    "data" : [
        "wizard/wizard_run_view.xml",
        "security/security.xml",
        "security/ir.model.access.csv",
        "fiscalyear_closing_workflow.xml",
        "fiscalyear_closing_view.xml",
        "hide_account_wizards.xml",
    ],
    "active": False,
    "installable": True,
    'images': [
        'images/l10n_es_fiscal_year_closing.png',
    ],
}

