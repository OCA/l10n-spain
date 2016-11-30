# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2011
#        Pexego Sistemas Informáticos. (http://pexego.es) All Rights Reserved
#        Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#
#    Adaptado a la versión 7.0 por:
#        Juanjo Algaz <juanjoa@malagatic.com>   www.malagatic.com
#        Joaquín Gutierrez <joaquing.pedrosa@gmail.com>   gutierrezweb.es
#        Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>   serviciosbaeza.com
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
    "name": "Informes de cuentas anuales españoles",
    "version": "8.0.0.1.0",
    "author": "Pexego, Zikzakmedia,Odoo Community Association (OCA)",
    "contributors": [
        "Juanjo Algaz <juanjoa@malagatic.com>",
        "Joaquín Gutierrez <joaquing.pedrosa@gmail.com>",
        "Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>",
    ],
    "license": "AGPL-3",
    "website": "http://www.pexego.es",
    "category": "Localisation/Accounting",
    "description": """
Informes de cuentas anuales oficiales españoles.
================================================

Incluye las siguientes plantillas para el motor de informes de cuentas provisto
por el módulo *account_balance_reporting*:

    * Balance PYMEs (PGCE 2008)
    * Cuenta de pérdidas y ganancias PYMEs (PGCE 2008)
    * Balance abreviado (PGCE 2008)
    * Cuenta de pérdidas y ganancias abreviado (PGCE 2008)
    * Balance normal (PGCE 2008)
    * Cuenta de pérdidas y ganancias completo (PGCE 2008)
    * Estado de ingresos y gastos reconocidos (PGCE 2008)

Las plantillas están basadas en los modelos para el depósito de cuentas anuales
del Registro Mercantil:

* *Normal*: http://www.mjusticia.gob.es/cs/Satellite/Portal/1292427306020
* *Abreviado*: http://www.mjusticia.gob.es/cs/Satellite/Portal/1292427306005
* *PYMEs*: http://www.mjusticia.gob.es/cs/Satellite/Portal/1292427306035
    """,
    "depends": [
        'l10n_es',
        'account_balance_reporting',
    ],
    "demo": [],
    "data": [
        'data/balance_pymes.xml',
        'data/pyg_pymes.xml',
        'data/balance_abreviado.xml',
        'data/pyg_abreviado.xml',
        'data/balance_normal.xml',
        'data/pyg_normal.xml',
        'data/estado_ingresos_gastos_normal.xml',
    ],
    'installable': False,
}
