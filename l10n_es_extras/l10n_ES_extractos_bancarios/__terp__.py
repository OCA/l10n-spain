# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
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
    "name" : "Importación de extractos bancarios C43",
    "version" : "1.0",
    "author" : "Zikzakmedia SL",
    "category" : "Localisation/Accounting",
    "description" : """Módulo para la importación de extractos bancarios según la norma C43 de la Asociación Española de la Banca.

Añade un asistente a los extractos bancarios para realizar la importación. El fichero importado queda como fichero adjunto al extracto en cuestión.
Permite definir las cuentas contables por defecto que se asociarán a los conceptos definidos en los fichero de extractos bancarios C43.

La búsqueda de la empresa se hace a partir de:
    1) La referencia2 del registro del extracto que acostumbra a ser la referencia de la operación que da la empresa. Se busca un apunte no conciliado con la misma referencia.
    2) El CIF/NIF que se encuentra en:
      - Los 9 primeros caracteres de l['referencia1'] del registro del extracto (Banc Sabadell)
      - Los 9 primeros caracteres de l['conceptos'] del registro del extracto (La Caixa)
      - Los caracteres [21:30] de l['conceptos'] (Caja Rural del Jalón)
      - Si otros bancos o cajas guardan el CIF en otro lugar contactar con el autor/equipo de localización para poderlo añadir o implementar una forma flexible de definirlo.
    3) Búsqueda en los apuntes no conciliados por importe
Si no se encuentra la empresa se asigna la cuenta contable que se haya definido por defecto para el concepto de ese registro.

Elimina el precálculo del importe de la línea del extracto bancario cuando se modifica la empresa (ya que los importes importados ya son los correctos)

El módulo añade un asistente en Gestión financiera/Configuración/Extractos bancarios C43 para la importación de los conceptos de extractos que se debe ejecutar una vez creado el plan de cuentas con el asistente correspondiente y con el módulo l10n_chart_ES previamente instalado.
""",
    "website" : "www.zikzakmedia.com",
    "license" : "GPL-3",
    "depends" : ["base","account","l10n_chart_ES",],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
        "extractos_view.xml",
        "extractos_wizard.xml",
        "security/ir.model.access.csv",
        ],
    "installable" : True,
    "active" : False,
}
