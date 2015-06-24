# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 Ting (http://www.ting.es) All Rights Reserved.
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
    'author': "Acysos S.L., "
              "Ting, "
              "Nan-tic, "
              "OpenMind Systems, "
              "Serv. Tecnol. Avanzados - Pedro M. Baeza, "
              "Odoo Community Association (OCA)",
    'website': 'https://github.com/OCA/l10n-spain',
    'category': 'Localisation/Accounting',
    'description': '''
Módulo para la presentación del modelo 340. Exportación a formato AEAT. Libro
de IVA

Los impuestos incluidos en este modelo se indican en el Código base cuenta. Por
defecto actualiza todos los código base que deban incluirse.
Si el plan contable esta instalado recuerde utilizar account_chart_update para
actualizar
los códigos. Contabilidad y Finanzas -> Configuración -> Contabilidad
Financiera -> Actualizar plan contable a partir de una plantila de plan
contable

Búsqueda de facturas emitidas y recibidas.
Exportación a formato de AEAT de facturas emitidas y recibidas.
Exportación de facturas con varios tipos impositivos. Clave de operación C.
Facturas intracomunitarias excepto las operaciones a las que hace referencia el
artículo 66 del RIVA que tienen un tratamiento especial.
Facturas rectificativas.
Facturas resumen de tiques.
Permite imprimir el libro de IVA, basado en la misma legislación.

---- COSAS PENDIENTES (TODO LIST) ---------------------------------------------

Facturas bienes de inversión
Facturas intracomunitarias. Operaciones a las que hace referencia el artículo
66 del RIVA.
Asientos contables de resumen de tiques
Exportación de asientos resumen de facturas
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
        'views/mod340_view.xml',
        'security/ir.model.access.csv',
        'views/res_partner_view.xml',
        'data/mod340_sequence.xml',
        'views/account_invoice_view.xml',
        'views/account_view.xml',
        'data/taxes_data.xml',
    ],
    'installable': True,
}
