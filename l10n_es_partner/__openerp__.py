# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008 Spanish Localization Team
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
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
    "name" : "Adaptación de partner para Estado Español",
    "version" : "1.0",
    "author" : "Spanish Localization Team",
    "category" : "Localisation/Europe",
    "description": """Funcionalidades:
    * Añade el campo *Nombre Comercial* a las empresas
    * Añades campos nombre largo, CIF y web a los bancos
    * Añade datos de 191 bancos y cajas españolas extraídos del registro oficial del Banco de España
    * Permite validar las cuentas bancarias, para ello añade un campo de país a los bancos de las empresas

Funcionamiento de la validación de la cuenta bancaria:
    * Se descartan todos los caracteres que no sean dígitos del campo número de cuenta.
    * Si los dígitos son 18 calcula los dos dígitos de control
    * Si los dígitos son 20 calcula los dos dígitos de control e ignora los actuales
        Presenta el resultado con el formato "1234 5678 06 1234567890"
    * Si el número de dígitos es diferente de 18 0 20 deja el valor inalterado
NOTA
Se ha eliminado la validación de CIF/NIF españoles, pues el módulo base_vat de OpenERP 5.0 añade un campo CIF/NIF en la pestaña de contabilidad de las empresas y la validación automática de los CIF de 27 paises europeos. Los CIFs deben introducirse añadiendo al principio los 2 caracteres que identifican cada país en mayúsculas (ES para España), por ejemplo ESB64425879

NOTA: Éste módulo añade un asistente en Empresas/Configuración/Bancos para la importación de todos los bancos y cajas de España. Antes de ejecutar éste asistente deberá tener importadas las provincias disponibles en el módulo l10n_es_toponyms.
""",
    "license" : "GPL-3",
    "depends" : [
        "base",
        "base_iban",
        "l10n_es_toponyms",
        ],
    "init_xml" : [],
    "update_xml" : [
        "partner_es_view.xml",
        ],
    "active": False,
    "installable": True
}




