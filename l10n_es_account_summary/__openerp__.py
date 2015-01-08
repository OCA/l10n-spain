# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo - Account summary
#    Copyright (C) 2015 Luis Martinez Ontalba (www.tecnisagra.com).
#	 
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
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
##############################################################################

{
    "name": "Account summary",
    "version": "1.1",
    "author": "Luis Martinez Ontalba",
    "website": "http://www.tecnisagra.com",
    "category": "Enterprise Specific Modules",
    "description": """
	Este modulo crea un tablero de resumen de datos contables de interés:
		* Ingresos, gastos y resultado:
			* Agrupado por año fiscal
			* Agrupado por periodo fiscal en el año en curso
		* Activo a corto, pasivo a corto y fondo de maniobra 
	Al tablero se accede desde el menu:
        Contabilidad/Contabilidad/Resumen de cuentas
            """,
    "depends": [
        'account', 'l10n_es_account', 'account_payment'
    ],
    "init_xml": [
    ],
    "demo_xml": [
	],
    "update_xml": [
        'account_summary.xml',
	],
    "installable": True,
    "active": False,
}
