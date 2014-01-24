# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2011 Acysos S.L. (http://acysos.com) All Rights Reserved.
#                       Ignacio Ibeas <ignacio@acysos.com>
#    Copyright (c) 2011 NaN Projectes de Programari Lliure, S.L.
#                       http://www.NaN-tic.com
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

    _inherit = "l10n.es.aeat.report.export_to_boe"
    _name = "l10n.es.aeat.mod340.export_to_boe"
    _description = "Export AEAT Model 340 to BOE format"

    def _get_formated_declaration_record(self, report):
        """
        Returns a type 1, declaration/company, formated record.

        Format of the record:
            Tipo registro 1 – Registro de declarante:
            Posiciones 	Descripción
            1           Tipo de Registro
            2-4 	Modelo Declaración
            5-8 	Ejercicio
            9-17 	NIF del declarante
            18-57 	Apellidos y nombre o razón social del declarante
            58          Tipo de soporte
            59-67 	Teléfono contacto
            68-107      Apellidos y nombre contacto
            108-120 	Número identificativo de la declaración
            121-122 	Declaración complementaria o substitutiva
            123-135 	Número identificativo de la declaración anterior
            136-137     Periodo
            138-146 	Número total de registros
            147-164 	Importe total de la base imponible
            165-182 	Importe Total de la cuota del impuesto
            183-200 	Importe total de las facturas
            201-390 	Blancos
            391-399 	NIF del representante legal
            400-415 	Sello electrónico
            416-500 	Blancos
        """
        text = ''

        text += '1'                                           # Tipo de Registro
        text += '340'                                         # Modelo Declaración
        text += self._formatString(report.fiscalyear_id.code, 4)   # Ejercicio
        text += self._formatString(report.company_vat, 9)          # NIF del declarante
        text += self._formatString(report.company_id.name, 40)     # Apellidos y nombre o razón social del declarante
        text += self._formatString(report.support_type, 1)         # Tipo de soporte
        text += self._formatString(report.contact_phone, 9)       # Persona de contacto (Teléfono)
        text += self._formatString(report.name_contact, 40)        # Persona de contacto (Apellidos y nombre)
        text += self._formatNumber(report.number, 13)              # Número identificativo de la declaración
        if (report.type == 'C'): text += 'C'                       # Declaración complementaria
        else: text += ' '
        if (report.type == 'S'): text += 'S'                       # Declaración substitutiva
        else: text += ' '
        text += self._formatNumber(report.previous_number, 13)     # Número identificativo de la declaración anterior
        text += self._formatString(report.period,2)     # Periodo
        text += self._formatNumber(report.number_records, 9)          # Número total de registros
        text += self._formatNumber(report.total_taxable, 15, 2,True)       # Importe total de la base imponible
        text += self._formatNumber(report.total_sharetax, 15, 2,True)      # Importe Total de la cuota del impuesto
        text += self._formatNumber(report.total, 15, 2,True)      # Importe total de las facturas
        text += 190*' '                                       # Blancos
        text += self._formatString(report.representative_vat, 9)   # NIF del representante legal
        text += self._formatString(report.ean13, 17)   # Sello electrónico
        text += 84*' '                                        # Blancos
        text += '\r\n'

        assert len(text) == 502, _("The type 1 record must be 500 characters long")
        return text
    
    def _get_formated_invoice_issued(self, cr, uid, report, invoice_issued):
        """
        Returns a type 2, invoice issued, formated record

        Format of the record:
            Tipo de Registro 2 – Registro de facturas emitidas
            Posiciones  Descripción
            1           Tipo de Registro
            2-4         Modelo Declaración
            5-8         Ejercicio
            9-17        NIF del declarante
            18-26       NIF del declarado
            27-35       NIF del representante legal
            36-75       Apellidos y nombre, razón social o denominación del declarado
            76-77       Código país
            78          Clave de identificación en el país de residencia
            79-95       Número de identificación fiscal en el país de residencia. TODO de momento blancos.
            96-98       Blancos
            99          Clave tipo de libro. Constante 'E'.
            100         Clave de operación. Constante ' ' para un solo tipo de IVA. Constante 'C' para varios tipos de IVA. TODO Resto de operaciones. Varios tipos impositivos.
            101-108     Fecha de expedición
            109-116     Fecha de operación. Se consigna la misma que expedición. TODO. Fecha del uso del bien.
            117-121     Tipo impositivo
            122-135     Base imponible
            136-149     Cuota del impuesto
            150-163     Importe total de la factura
            164-177     Base imponible a coste. TODO de momento 0.
            178-217     Identificación de la factura
            218-235     Número de registro TODO No se exactamente que es
            236-243     Número de facturas. Siempre 1. TODO Resumenes de facturas o tickets. Clave A o B.
            244-245     Número de registro. Siempre 1. TODO Facturas con varios asientos. Clave C.
            246-325     Intervalo de acumulación. Vacio. TODO Intervalo de resumenes de facturas o tickets.
            326-365     Identificación de la factura rectificativa. TODO.
            366-370     Tipo recargo de equivalencia. TODO.
            371-384     Cuota recargo de equivalencia. TODO.
            385         Situación del Inmueble #TODO  2012
            386-410     Referencia Catastral #TODO 2012
            411-425     Importe Percibido en Metálico #TODO 2012
            426-429     Ejercicio ( cifras del ejercicio en el que se hubieran declarado las operaciones que dan origen al cobro ) #TODO 2012
            430-444     Importe percibido por transmisiones de Inmuebles sujetas a IVA. #TODO 2012
            445-500     BLANCOS            
            

        """
        text = ''
        for tax_line in invoice_issued.tax_line_ids:
    
            text += '2'                                                     # Tipo de Registro
            text += '340'                                                   # Modelo Declaración
            text += self._formatString(report.fiscalyear_id.code, 4)             # Ejercicio
            text += self._formatString(report.company_vat, 9)                    # NIF del declarante
            if invoice_issued.partner_country_code == 'ES': text += self._formatString(invoice_issued.partner_vat, 9)            # NIF del declarado
            else: text += self._formatString(' ', 9) 
            text += self._formatString(invoice_issued.representative_vat, 9)     # NIF del representante legal
            text += self._formatString(invoice_issued.partner_id.name, 40)       # Apellidos y nombre, razón social o denominación del declarado
            text += self._formatString(invoice_issued.partner_country_code, 2)     # Código país
            text += self._formatNumber(invoice_issued.partner_id.vat_type, 1)   # Clave de identificación en el país de residencia
            if invoice_issued.partner_country_code != 'ES':                     # Número de identificación fiscal en el país de residencia.
                text += self._formatString(invoice_issued.partner_country_code, 2)
                text += self._formatString(invoice_issued.partner_vat, 15)
            else: text += 17*' '
            text += 3*' '                                                     # Blancos
            text += 'E'                                                         # Clave tipo de libro. Constante 'E'.
            
            if invoice_issued.invoice_id.origin_invoices_ids:               # Clave de operación
                text +='D'
            elif len(invoice_issued.tax_line_ids) > 1: text += 'C'
            elif invoice_issued.invoice_id.is_ticket_summary == 1: text += 'B'
            else: text += ' '
            
            text += self._formatNumber(invoice_issued.invoice_id.date_invoice.split('-')[0],4)
            text += self._formatNumber(invoice_issued.invoice_id.date_invoice.split('-')[1],2)
            text += self._formatNumber(invoice_issued.invoice_id.date_invoice.split('-')[2],2)    # Fecha de expedición
            text += self._formatNumber(invoice_issued.invoice_id.date_invoice.split('-')[0],4)
            text += self._formatNumber(invoice_issued.invoice_id.date_invoice.split('-')[1],2)
            text += self._formatNumber(invoice_issued.invoice_id.date_invoice.split('-')[2],2)    # Fecha de operación
            
            text += self._formatNumber(tax_line.tax_percentage*100,3,2)                        #Tipo impositivo
            text += self._formatNumber(tax_line.base_amount, 11,2,True)         # Base imponible
            text += self._formatNumber(tax_line.tax_amount, 11,2,True)         # Cuota del impuesto
            text += self._formatNumber(tax_line.tax_amount+tax_line.base_amount, 11,2,True)         # Importe total de la factura
            text += ' '+self._formatNumber(0, 11,2)                             # Base imponible a coste.
            text += self._formatString(invoice_issued.invoice_id.number, 40)  # Identificación de la factura
            text += self._formatString(self.pool.get('ir.sequence').get(cr, uid, 'mod340'),18)  # Número de registro
            if invoice_issued.invoice_id.is_ticket_summary == 1:           # Número de facturas
                text += self._formatNumber(invoice_issued.invoice_id.number_tickets, 8)
            else: text += self._formatNumber(1, 8)
            text += self._formatNumber(len(invoice_issued.tax_line_ids), 2)  # Número de registros (Desglose)
            if invoice_issued.invoice_id.is_ticket_summary == 1:      # Intervalo de identificación de la acumulación
                text += self._formatString(invoice_issued.invoice_id.first_ticket, 40)
                text += self._formatString(invoice_issued.invoice_id.last_ticket, 40)
            else: text += 80*' '
            text +=  self._formatString( ",".join( [x.number for x in  invoice_issued.invoice_id.origin_invoices_ids]) , 40 )   # Identificación factura rectificativa
            text += self._formatNumber(0, 5)  # Tipo Recargo de equivalencia
            text += ' '+self._formatNumber(0, 11,2)  # Couta del recargo de equivalencia
            text += '0'  #Situación del Inmueble #TODO  2012
            text += 25*' ' #Referencia Catastral #TODO 2012
            text += 15*'0'  #Importe Percibido en Metálico #TODO 2012
            text += 4*'0' #Ejercicio ( cifras del ejercicio en el que se hubieran declarado las operaciones que dan origen al cobro ) #TODO 2012
            text += 15*'0' #Importe percibido por transmisiones de Inmuebles sujetas a IVA. #TODO 2012            
            text += 56*' '                                                     # Blancos
            text += '\r\n'
        assert len(text) == 502*len(invoice_issued.tax_line_ids), _("The type 2 issued record must be 500 characters long for each Vat registry")
        return text
    
    def _get_formated_invoice_received(self, cr, uid, report, invoice_received):
        """
        Returns a type 2, invoice received, formated record

        Format of the record:
            Tipo de Registro 2 – Registro de facturas recibidas
            Posiciones  Descripción
            1           Tipo de Registro
            2-4         Modelo Declaración
            5-8         Ejercicio
            9-17        NIF del declarante
            18-26       NIF del declarado
            27-35       NIF del representante legal
            36-75       Apellidos y nombre, razón social o denominación del declarado
            76-77       Código país
            78          Clave de identificación en el país de residencia
            79-95       Número de identificación fiscal en el país de residencia. TODO de momento blancos.
            96-98       Blancos
            99          Clave tipo de libro. Constante 'R'.
            100         Clave de operación. Constante ' ' para un solo tipo de IVA. Constante 'C' para varios tipos de IVA. TODO Resto de operaciones. Varios tipos impositivos.
            101-108     Fecha de expedición
            109-116     Fecha de operación. Se consigna la misma que expedición. TODO. Fecha del uso del bien.
            117-121     Tipo impositivo
            122-135     Base imponible
            136-149     Cuota del impuesto
            150-163     Importe total de la factura
            164-177     Base imponible a coste. TODO de momento 0.
            178-217     Identificación de la factura
            218-235     Número de registro TODO No se exactamente que es
            236-243     Número de facturas. Siempre 1. TODO Resumenes de facturas o tickets. Clave A o B.
            244-245     Número de registro. Siempre 1. TODO Facturas con varios asientos. Clave C.
            246-335     Intervalo de acumulación. Vacio. TODO Intervalo de resumenes de facturas o tickets.
            336-349     Cuota deducible. TODO.
            350-500     Blancos
            

        """
        text = ''
        for tax_line in invoice_received.tax_line_ids:
    
            text += '2'                                                     # Tipo de Registro
            text += '340'                                                   # Modelo Declaración
            text += self._formatString(report.fiscalyear_id.code, 4)             # Ejercicio
            text += self._formatString(report.company_vat, 9)                    # NIF del declarante
            if invoice_received.partner_country_code == 'ES': text += self._formatString(invoice_received.partner_vat, 9)            # NIF del declarado
            else: text += self._formatString(' ', 9) 
            text += self._formatString(invoice_received.representative_vat, 9)     # NIF del representante legal
            text += self._formatString(invoice_received.partner_id.name, 40)       # Apellidos y nombre, razón social o denominación del declarado
            text += self._formatString(invoice_received.partner_country_code, 2)     # Código país
            text += self._formatNumber(invoice_received.partner_id.vat_type, 1)   # Clave de identificación en el país de residencia
            if invoice_received.partner_country_code != 'ES':                     # Número de identificación fiscal en el país de residencia.
                text += self._formatString(invoice_received.partner_country_code, 2)
                text += self._formatString(invoice_received.partner_vat, 15)
            else: text += 17*' '
            text += 3*' '                                                     # Blancos
            text += 'R'                                                         # Clave tipo de libro. Constante 'E'.
            
            if invoice_received.invoice_id.operation_key == 'I':
                text +='I'
            elif len(invoice_received.tax_line_ids) > 1: text += 'C'              # Clave de operación
            else: text += ' '
            
            text += self._formatNumber(invoice_received.invoice_id.date_invoice.split('-')[0],4)
            text += self._formatNumber(invoice_received.invoice_id.date_invoice.split('-')[1],2)
            text += self._formatNumber(invoice_received.invoice_id.date_invoice.split('-')[2],2)    # Fecha de expedición
            text += self._formatNumber(invoice_received.invoice_id.date_invoice.split('-')[0],4)
            text += self._formatNumber(invoice_received.invoice_id.date_invoice.split('-')[1],2)
            text += self._formatNumber(invoice_received.invoice_id.date_invoice.split('-')[2],2)    # Fecha de operación
            
            text += self._formatNumber(tax_line.tax_percentage*100,3,2)                        #Tipo impositivo
            text += self._formatNumber(tax_line.base_amount, 11,2,True)         # Base imponible
            text += self._formatNumber(tax_line.tax_amount, 11,2,True)         # Cuota del impuesto
            text += self._formatNumber(tax_line.tax_amount+tax_line.base_amount, 11,2,True)         # Importe total de la factura
            text += ' '+self._formatNumber(0, 11,2)                             # Base imponible a coste.
            text += self._formatString(invoice_received.invoice_id.reference, 40)  # Identificación de la factura
            text += self._formatString(self.pool.get('ir.sequence').get(cr, uid, 'mod340'),18)  # Número de registro
            text += self._formatNumber(1, 18) # Número de facturas
            text += self._formatNumber(len(invoice_received.tax_line_ids), 2)  # Número de registros (Desglose)
            text += 80*' '  # Intervalo de identificación de la acumulación
            text += ' '+self._formatNumber(0, 11,2)  # Cuota deducible
            text += 151*' '                                                     # Blancos
            text += '\r\n'
        
        assert len(text) == 502*len(invoice_received.tax_line_ids), _("The type 2 received record must be 500 characters long for each Vat registry")
        return text
    
    def _get_formated_other_records(self,cr,uid,report):
        file_contents = ''

        for invoice_issued in report.issued:
            file_contents += self._get_formated_invoice_issued(cr,uid,report, invoice_issued)

        for invoice_received in report.received:
            file_contents += self._get_formated_invoice_received(cr,uid,report, invoice_received)

        return file_contents
    

    def _export_boe_file(self, cr, uid, ids, report, model=None, context=None):
        """
        Action that exports the data into a BOE formated text file
        """
        if context is None:
            context = {}
        
        file_contents = ''

        ##
        ## Add header record
        file_contents += self._get_formated_declaration_record(report)

        ##
        ## Adds other fields
        file_contents += self._get_formated_other_records(cr,uid,report)

        ##
        ## Generate the file and save as attachment
        file = base64.encodestring(file_contents)

        file_name = _("340_report_%s.txt") % (time.strftime(_("%Y-%m-%d")))
        self.pool.get("ir.attachment").create(cr, uid, {
            "name" : file_name,
            "datas" : file,
            "datas_fname" : file_name,
            "res_model" : "l10n.es.aeat.mod340",
            "res_id" : ids and ids[0]
        }, context=context)

l10n_es_aeat_mod340_export_to_boe()
