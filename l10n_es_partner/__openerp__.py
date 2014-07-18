# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008 Spanish Localization Team
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com)
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2013 Acysos S.L. (http://acysos.com)
#                       Ignacio Ibeas <ignacio@acysos.com>
#    Copyright (c) 2013 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                       Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
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
    "name" : "Adaptación de los clientes, proveedores y bancos para España",
    "version" : "1.1",
    "author" : "Spanish localization team",
    "website" : "https://github.com/OCA/l10n-spain",
    "contributors": [
        'Jordi Esteve <jesteve@zikzakmedia.com>',
        'Ignacio Ibeas <ignacio@acysos.com>',
        'Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>',
    ],
    "category" : "Localisation/Europe",
    "description": """
Funcionalidad:
--------------

 * Añade el campo *Nombre comercial* a las empresas y permite buscar por él.
 * Convierte el NIF a mayúsculas.
 * Añade los campos nombre largo, NIF y web a los bancos.
 * Añade los datos de los bancos españoles extraídos del registro oficial del
   Banco de España (http://goo.gl/mtx6ic). Ult. actualización: 2013.
 * Permite validar las cuentas bancarias españolas. Para ello, se añade un
   campo de país a las cuentas bancarias de las empresas y se realizan
   validaciones cuando el país es España.


Funcionamiento de la validación de la cuenta bancaria para cuentas españolas:
-----------------------------------------------------------------------------

 * Se comprueba si la cuenta consta de 20 dígitos (con o sin espacios).
 * Si no los tiene, se devuelve un error de longitud incorrecta.
 * Si los dígitos son 20, se calculan los dos dígitos de control (DC) y se
   comprueba que coinciden con los introducidos.
 * Si el DC no coincide, se devuelve un error de que la cuenta es incorrecta.
 * Si el DC es correcto, presenta el resultado con el formato
   "1234 5678 06 1234567890"


Funcionamiento de la validación de la cuenta bancaria para cuentas IBAN:
------------------------------------------------------------------------

 * Se limpia la cuenta de espacios.
 * Se divide lo introducido en bloques de 4 caracteres.
""",
    "license" : "AGPL-3",
    "depends" : [
        "base",
        "base_iban",
        "l10n_es_toponyms",
    ],
    "data" : [
        "l10n_es_partner_view.xml",
        "wizard/l10n_es_partner_wizard.xml"
    ],
    "installable": True,
}
