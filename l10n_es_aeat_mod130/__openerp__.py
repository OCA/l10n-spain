# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c):
#       2014      Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                 Pedro M. Baeza <pedro.baeza@serviciobaeza.com>
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
    "name": "AEAT modelo 130",
    "version": "0.8",
    "author": "Serv. Tecnol. Avanzados - Pedro M. Baeza,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "http://www.serviciosbaeza.com",
    "category": "Localisation/Accounting",
    "description": """
Modelo 130 de la AEAT
=====================

Módulo para la presentación del modelo 130 (Pago fraccionado IRPF - Impuesto
sobre la Renta de las Personas Físicas - para empresarios y profesionales en
estimación directa) de la Agencia Española de Administración Tributaria.

Instrucciones del modelo: http://goo.gl/StTY2h

Incluye la exportación al formato BOE para su uso telemático.

**AVISO**: Este modelo no cubre el 100% de las posibilidades que se pueden
dar en la declaración, por lo que se exime a los desarrolladores de cualquier
responsabilidad derivada de su uso. Carencias conocidas:

* La casilla [02] no se calculará correctamente si se incluyen en la partida
  de gastos (familia de cuentas 6), gastos que no son deducibles.
* En la casilla [04], no se tienen en cuenta deducciones para rentas obtenidas
  en Ceuta o Melilla.
* No se tienen en cuenta las retenciones e ingresos a cuenta soportados sobre
  los rendimientos procedentes de las actividades económicas (casilla [06]).
* No se pueden realizar declaraciones para actividades agrícolas, ganaderas,
  forestales y pesqueras (casillas [08] a [11]).
* No se pueden aplicar las deducciones correspondientes por el artículo 80 bis
  (casilla [13]).
* No se pueden deducir resultados negativos de anteriores declaraciones
  (casilla [15]).
    """,
    "depends": [
        "l10n_es_aeat",
    ],
    "data": [
        "wizard/export_mod130_to_boe.xml",
        "mod130_view.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
}
