# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 Ting (http://www.ting.es)
#    Copyright (c) 2011-2013 Acysos S.L. (http://acysos.com)
#                       Ignacio Ibeas Izquierdo <ignacio@acysos.com>
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
    'name': 'Generación de fichero modelo 340 y libro de IVA',
    'version': '2.0',
    'author': "Acysos S.L., Francisco Pascual (Ting), "
              "Nan-tic, "
              "Odoo Community Association (OCA)",
    'website': 'www.acysos.com, www.ting.es, www.nan-tic.com',
    'category': 'Localisation/Accounting',
    'description': '''
Módulo para la presentación del modelo 340. Exportación a formato AEAT. Libro
de IVA.

Los impuestos incluidos en este modelo se indican en el Código base cuenta.
Por defecto actualiza todos los código base que deban incluirse.
Si el plan contable esta instalado recuerde utilizar _account_chart_update_
para actualizar los códigos. _Contabilidad y Finanzas -> Configuración -> _
_Contabilidad Financiera -> Actualizar plan contable a partir de una _
_plantila de plan contable_.

* Búsqueda de facturas emitidas y recibidas.
* Exportación a formato de AEAT de facturas emitidas y recibidas.
* Exportación de facturas con varios tipos impositivos. Clave de operación C.
* Facturas intracomunitarias excepto las operaciones a las que hace referencia
  el artículo 66 del RIVA que tienen un tratamiento especial.
* Facturas rectificativas.
* Facturas resumen de tiques.
* Permite imprimir el libro de IVA, basado en la misma legislación.

--- COSAS PENDIENTES (TODO LIST) ----------------------------------------------

* Facturas bienes de inversión.
* Facturas intracomunitarias. Operaciones a las que hace referencia el artículo
  66 del RIVA.
* Asientos contables de resumen de tiques.
* Exportación de asientos resumen de facturas.
''',
    'license': 'AGPL-3',
    'depends': [
        'account',
        'base_vat',
        'l10n_es',
        'l10n_es_aeat',
        'account_refund_original',
        'account_chart_update',
    ],
    'data': [
        'report/report_view.xml',
        'wizard/export_mod340_to_boe.xml',
        'mod340_view.xml',
        'mod340_workflow.xml',
        'security/ir.model.access.csv',
        'res_partner_view.xml',
        'mod340_sequence.xml',
        'account_invoice_view.xml',
        'account_view.xml',
        'taxes_data.xml',
    ],
    'installable': True,
}
