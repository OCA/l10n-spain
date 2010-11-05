# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Alejandro Sanchez (http://www.asr-oss.com) All Rights Reserved.
#                       Alejandro Sanchez <alejandro@asr-oss.com>
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
    "name" : "Generación de fichero modelo 347",
    "version" : "1.0",
    "author" : "ASR-OSS, Pexego",
    "category" : "Localisation/Accounting",
    "description" : """
Módulo para la presentación del Modelo AEAT 347 (Declaración Anual de Operaciones con Terceros)

Basado en la Orden EHA/3012/2008, de 20 de Octubre, por el que se aprueban los diseños físicos y lógicos del 347.

De acuerdo con la normativa de la Hacienda Española, están obligados a presentar el modelo 347:
    * Todas aquellas personas físicas o jurídicas, de naturaleza pública o
        privada que desarrollen actividades empresariales o profesionales,
        siempre y cuando hayan realizado operaciones que, en su conjunto,
        respecto de otra persona o Entidad, cualquiera que sea su naturaleza
        o carácter, hayan superado la cifra de 3.005,06€ durante el año natural
        al que se refiere la declaración. Para el cálculo de la cifra de
        3.005,06 € se computan de forma separada las entregas de bienes
        y servicios y las adquisiciones de los mismos.

De acuerdo con la normativa no están obligados a presentar el modelo 347:
    * Quienes realicen en España actividades empresariales o profesionales sin
        tener en territorio español la sede de su actividad, un establecimiento
        permanente o su domicilio fiscal.
    * Las personas físicas y entidades en régimen de atribución de rentas en
        el IRPF, por las actividades que tributen en dicho impuesto por el
        régimen de estimación objetiva y, simultáneamente, en el IVA por los
        régimenes especiales simplificados o de la agricultura, ganadería
        y pesca o recargo de equivalencia, salvo las operaciones que estén
        excluidas de la aplicación de los expresados regímenes.
    * Los obligados tributarios que no hayan realizado operaciones que en su
        conjunto superen la cifra de 3.005,06€
    * Los obligados tributarios que hayan realizado exclusivamente operaciones
        no declarables.
    * Los obligados tributarios que deban informar sobre las operaciones
        incluidas en los libros registro de IVA (modelo 340) salvo que realicen
        operaciones que expresamente deban incluirse en el modelo 347.

(http://www.boe.es/boe/dias/2008/10/23/pdfs/A42154-42190.pdf)

Desarrollado por Alejandro Sanchez (ASR-OSS, www.asr-oss.com)
        y Borja López Soilán (Pexego, www.pexego.es)
    """,
    "website" : "www.asr-oss.com",
    "license" : "GPL-3",
    "depends" : [
                    'account',
                    'base_vat',
                    'account_invoice_currency',
                ],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
                    'mod347_workflow.xml',
                    'mod347_wizard.xml',
                    'mod347_report.xml',
                    'mod347_view.xml',
                    'partner_view.xml',
                    'account_journal_view.xml',
                    'security/ir.model.access.csv',
                    ],
    "installable" : True,
    "active" : False,
}
