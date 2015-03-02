# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C)
#        2004-2011: Pexego Sistemas Informáticos. (http://pexego.es)
#        2013:      Top Consultant Software Creations S.L.
#                   (http://www.topconsultant.es/)
#
#    Autores originales: Luis Manuel Angueira Blanco (Pexego)
#                        Omar Castiñeira Saavedra(omar@pexego.es)
#    Migración OpenERP 7.0: Ignacio Martínez y Miguel López.
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
    "name": "AEAT modelo 349",
    "version": "2.0",
    "author": "Pexego,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    'contributors': [
        'Miguel López (Top Consultant)',
        'Ignacio Martínez (Top Consultant)',
        'Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>',
    ],
    "category": 'Localisation/Accounting',
    "description": """
Módulo para la presentación del Modelo AEAT 349 (Declaración Recapitulativa de
Operaciones Intracomunitarias)

Basado en la Orden EHA/769/2010 por el que se aprueban los diseños físicos y
lógicos del 349.

De acuerdo con la normativa de la Hacienda Española, están obligados a
presentar el modelo 349:

 * Todos aquellos sujetos pasivos del Impuesto sobre el Valor Añadido que hayan
   realizado las operaciones previstas en el artículo 79 del Reglamento del
   Impuesto sobre el Valor Añadido, es decir, quienes adquieran o vendan bienes
   a empresas situadas en países miembros de la UE, sino también aquellos que
   presten servicios a miembros de la UE y cumplan con las siguientes
   condiciones:

  - Que conforme a las reglas de la localización aplicables a las
    mismas, no se entiendan prestadas en el territorio de aplicación del
    impuesto.

  - Que estén sometidas efectivamente a gravamen de otro Estado miembro.

  - Que su destinatario sea un empresario o profesional actuando como
    tal y radique en dicho Estado miembro la sede de su actividad
    económica, o tenga en el mismo un establecimiento permanente o, en su
    defecto, el lugar de su domicilio o residencia habitual, o que dicho
    destinatario sea una persona jurídica que no actúe como empresario o
    profesional pero tenga asignado un número de identificación a efectos
    del Impuesto suministrado por ese Estado miembro.

  - Que el sujeto pasivo sea dicho destinatario.

    El período de declaración comprenderá, con carácter general las
    operaciones realizadas en cada mes natural, y se presentará durante los
    veinte primeros días naturales del mes inmediato siguiente al
    correspondiente período mensual. No obstante, la presentación podrá ser
    bimestral, trimestral o anual en los siguientes supuestos:

 * Bimestral: Si al final del segundo mes de un trimestre natural el
   importe total de las entregas de bienes y prestaciones de servicios que
   deban consignarse en la declaración recapitulativa supera 100.000 euros
   (a partir de 2012, el umbral se fija en 50.000 euros).

 * Trimestral: Cuando ni durante el trimestre de referencia ni en cada uno
   de los cuatro trimestres naturales anteriores el importe total de las
   entregas de bienes y prestaciones de servicios que deban consignarse en la
   declaración recapitulativa sea superior a 100.000 euros.

 * Anual: En los treinta primeros días de enero del año siguiente ( la
   primera sería en enero de 2011) si el importe total de las entregas de
   bienes o prestaciones de servicios  del año ( excluido IVA), no supera los
   35.000 € y el importe total de las entregas de bienes a otro Estado
   Miembro (salvo medios de transporte nuevos) exentas de IVA no sea superior
   a 15.000 €.
    """,
    'website': 'http://www.pexego.es',
    "depends": [
        "account",
        "account_invoice_currency",
        "account_refund_original",
        "l10n_es",
        "l10n_es_aeat",
    ],
    'data': [
        "wizard/export_mod349_to_boe.xml",
        "account_fiscal_position_view.xml",
        "account_invoice_view.xml",
        "mod349_view.xml",
        "report/mod349_report.xml",
        "security/ir.model.access.csv",
        "security/mod_349_security.xml",
        "data/assign_invoices_op_keys.xml",
    ],
    'installable': True,
}
