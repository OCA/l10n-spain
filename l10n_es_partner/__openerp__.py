# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008 Spanish Localization Team
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2013 Acysos S.L. (http://acysos.com) All Rights Reserved.
#                       Ignacio Ibeas <ignacio@acysos.com>
#    Copyright (c) 2013 Servicios Tecnológicos Avanzados (http://www.serviciosbaeza.com)
#                       Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
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
##############################################################################

{
    "name" : "Adaptación de los terceros para España",
    "version" : "1.0",
    "author" : "Spanish localization team",
    "website" : "https://launchpad.net/openerp-spain",
    "contributors": [
        'Jordi Esteve <jesteve@zikzakmedia.com>',
        'Ignacio Ibeas <ignacio@acysos.com>',
        'Pedro M. Baeza <pedro.baeza@serviciosbaeza.com',
    ],
    "category" : "Localisation/Europe",
    "description": """
Funcionalidades:
    * Añade el campo *Nombre comercial* a las empresas y permite buscar por él.
    * Convierte el NIF a mayúsculas.
    * Añade los campos nombre largo, NIF y web a los bancos.
    * Añade datos de 191 bancos y cajas españolas extraídos del registro oficial del Banco de España.
    * Permite validar las cuentas bancarias, para ello añade un campo de país a los bancos de las empresas.

Funcionamiento de la validación de la cuenta bancaria:
    * Se descartan todos los caracteres que no sean dígitos del campo número de cuenta.
    * Si los dígitos son 18, calcula los dos dígitos de control.
    * Si los dígitos son 20, calcula los dos dígitos de control e ignora los actuales.
    * Presenta el resultado con el formato "1234 5678 06 1234567890"
    * Si el número de dígitos es diferente de 18 0 20, deja el valor inalterado.
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
    "active": False,
    "installable": True
}

