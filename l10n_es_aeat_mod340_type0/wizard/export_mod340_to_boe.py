# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2013 Acysos S.L. (http://acysos.com) All Rights Reserved.
#                       Ignacio Ibeas <ignacio@acysos.com>
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

import base64
import time

from osv import osv
from tools.translate import _


class l10n_es_aeat_mod340_export_to_boe(osv.osv_memory):

    _inherit = "l10n.es.aeat.mod340.export_to_boe"

    def _get_formated_presenter_record(self, report):
        """
        Returns a type 0, declaration/presenter, formated record.
        Only for Comunidad Foral de Navarra

        Format of the record:
            Tipo registro 0 – Registro de presentador:
            Posiciones 	Descripción
            1           Tipo de Registro
            2-4 	Modelo Declaración
            5-8 	Ejercicio
            9-17 	NIF del presentador
            18-57 	Apellidos y nombre o razón social del presentador
            58-59       Domicilio - Siglas de la vía pública
            60-79       Domicilio - Nombre de la vía pública
            80-84       Domicilio - Número de la casa o punto kilométrico
            85-86       Domicilio - Escalera
            87-88       Domicilio - Piso
            89-90       Domicilio - Puerta
            91-95       Domicilio - Código postal
            96-107      Domicilio - Municipio del presentador
            108-109     Domicilio - Código provincia
            110-114     Total de declarantes
            115-123     Total de declarados
            124         Tipo de soporte
            125-133     Télefono de contacto
            134-173     Apellidos y nombre de la persona de contacto
            174-487     Relleno a blanco
            488-500     Sello electrónico
        """
        
        text = ''
        
        text += '0'                                           # Tipo de Registro
        text += '340'                                         # Modelo Declaración
        text += self._formatString(report.fiscalyear_id.code, 4)   # Ejercicio
        text += self._formatString(report.presenter_vat or '', 9)          # NIF del presentador
        text += self._formatString(report.presenter_name or '', 40)     # Apellidos y nombre del presentador
        text += self._formatString(report.presenter_address_acronym or '', 2)   # Siglas de la vía pública
        text += self._formatString(report.presenter_address_name or '', 20)   # Nombre de la vía pública
        text += self._formatNumber(report.presenter_address_number or 0, 5)  # Número de la casa
        text += self._formatString(report.presenter_address_stair or '', 2)   # Escalera
        text += self._formatString(report.presenter_address_floor or '', 2)   # Piso
        text += self._formatString(report.presenter_address_door or '', 2)   # Puerta
        text += self._formatNumber(int(report.presenter_city_id.zip or 0), 5)  # Código postal
        text += self._formatString(report.presenter_city_id.name or '', 12)  # Municipio
        if report.presenter_city_id:
            text += self._formatNumber(int(report.presenter_city_id.state_id.code), 2)  # Código postal
        else:
            text += 2*' '
        text += '00001'      # Numero total de declarantes, actualmente solo 1
        text += self._formatNumber(report.number_records, 9)   # Número total de registros
        text += self._formatString(report.support_type, 1)   # Tipo de soporte
        text += self._formatString(report.presenter_phone_contact or '', 9) # Persona de contacto (Teléfono)
        text += self._formatString(report.presenter_name_contact or '', 40) # Persona de contacto (Apellidos y nombre)
        text += 314*' '   # Blancos
        text += 13*' '   # Firma digital opcional, no implementado
        text += '\r\n'
        
        assert len(text) == 502, _("The type 0 record must be 500 characters long")
        return text
    

    def _export_boe_file(self, cr, uid, ids, report, model=None, context=None):
        """
        Action that exports the data into a BOE formated text file
        """
        if context is None:
            context = {}
        
        file_contents = ''
        
        ##
        ## Add record type 0, if company is in Comunidad Foral de Navarra
        file_contents += self._get_formated_presenter_record(report)

        ##
        ## Add header record
        file_contents += self._get_formated_declaration_record(report)

        ##
        ## Adds other fields
        file_contents += self._get_formated_other_records(cr,uid,report)

        ##
        ## Generate the file and save as attachment
        file = base64.encodestring(file_contents)
        
        # Delete old files
        obj_attachment = self.pool.get('ir.attachment')
        attachment_ids = obj_attachment.search(cr, uid, 
                                               [('name', '=', file_name), 
                                                ('res_model', '=', 'l10n.es.aeat.mod340')])
        if len(attachment_ids):
            obj_attachment.unlink(cr, uid, attachment_ids)

        file_name = _("340_report_%s.txt") % (time.strftime(_("%Y-%m-%d")))
        self.pool.get("ir.attachment").create(cr, uid, {
            "name" : file_name,
            "datas" : file,
            "datas_fname" : file_name,
            "res_model" : "l10n.es.aeat.mod340",
            "res_id" : ids and ids[0]
        }, context=context)

l10n_es_aeat_mod340_export_to_boe()
