# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 Ting (http://www.ting.es) All Rights Reserved.
#    Copyright (c) 2011 Acysos S.L. (http://acysos.com) All Rights Reserved
#                       Ignacio Ibeas Izquierdo <ignacio@acysos.com>
#                       
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
    "name" : "Generación de fichero modelo 340",
    "version" : "1.0",
    "author" : "Acysos S.L., Francisco Pascual (Ting)",
    "category" : "Localisation/Accounting",
    "description" : """
Módulo para la presentación del modelo 340. Exportación a formato AEAT.
********************* Esta versión se encuetra en desarrollo ************************
--- ESTADO ACTUAL -------------------------------------------------------------

Búsqueda de facturas emitidas y recibidas. Excluidas lineas de impuestos con IRPF.
Exportación a formato de AEAT de facturas emitidas y recibidas.
Exportación de facturas con varios tipos impositivos. Clave de operación C
Facturas intracomunitarias excepto las operaciones a las que hace referencia el artículo 66 del RIVA que tienen un tratamiento especial
Facturas rectificativas

--- COSAS PENDIENTES (TODO LIST) ----------------------------------------------

Facturas bienes de inversión
Facturas intracomunitarias. Operaciones a las que hace referencia el artículo 66 del RIVA.
Exportación de resúmenes de tiques
Exportación de asientos resumen de facturas

ADVERTENCIA: Los periodos de la empresas deben coincidir con los peridos de presentación de IVA.
""",
    "website" : "www.acysos.com, www.ting.es",
    "license" : "AGPL-3",
    "depends" : ["account",
                 "base_vat",
                 "l10n_es_aeat",
                 ],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : ['report/report_view.xml',"mod340_view.xml","mod340_workflow.xml","security/ir.model.access.csv", "res_partner_view.xml","mod340_sequence.xml","account_invoice_view.xml"],
    "installable" : True,
    "active" : False,
}
