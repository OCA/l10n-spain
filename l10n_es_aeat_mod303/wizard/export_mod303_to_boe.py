# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2013 Guadaltech. All Rights Reserved
#    Author: Alberto Martín Cortada
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


__author__ = "Alberto Martín Cortada"

import base64
import time
from datetime import datetime


from tools.translate import _
from osv import osv
from account.report.account_tax_report import tax_report 


class l10n_es_aeat_mod303_export_to_boe(osv.osv_memory):

    _inherit = "l10n.es.aeat.report.export_to_boe"
    _name = "l10n.es.aeat.mod303.export_to_boe"
    _description = "Export AEAT Model 303 to BOE format"


    def _get_formated_declaration(self,report):
        
        file_contents = ''
        
        ## cabecera 
        
        file_contents += "<T30301>"                 ## pos 1
        
        file_contents += ' '                        ## pos  9
        
        ## pos 10 
        ## tipo de declaración - "Para impresión, cualquier caracter Alfanumerico o 'N' si la autoliquidación se declara SIN ACTIVIDAD"
        
        file_contents += self._formatString("N" if report.sin_actividad else " ",1)  ## pos 10

        ## identificación (1)
        
        file_contents += self._formatString(report.company_vat, 9)       ## pos 19 # NIF del declarante
        
        file_contents += self._formatString(report.company_id.name, 30)  ## pos 49 # Apellidos o Razon Social.
        file_contents += self._formatString("", 15)                      ## pos 64 # Nombre

        file_contents += self._formatBoolean(report.devolucion_mensual, yes='1', no='2') # pos 65
        
        
        ## devengo (2)
        
        file_contents += self._formatNumber(report.fiscalyear_id.code, 4)             ## 69
        file_contents += self._formatString(report.period,2)                          ## 71
        
        
        assert len(file_contents) == 71, _("The identification (1) and income (2) must be 72 characters long")
        return file_contents        

    def _get_formated_vat(self,cr,uid,ids,report):
        
        
        model_report_obj = self.pool.get("l10n.es.aeat.mod303.report")
        file_contents = ''

        ## lines obtenido de account_tax_report
        
        lines = model_report_obj._get_report_lines(cr,uid,ids)
              
        ## IVA devengado
    
        # -- Regimen General y Recargo de Equivalencia - codes [1~18]
        
        for codes in [('[01]','[03]'),('[04]','[06]'),('[07]','[09]'), ## regimen general
                      ('[10]','[12]'),('[13]','[15]'),('[16]','[18]')]: ## recargo equivalencia
            
            base_imponible = lines.get(codes[0],0)
            cuota = lines.get(codes[1],0)
            
            file_contents += self._formatNumber(base_imponible, 15,2) # base imponible X %  -- codes [1,4,7,10,13,16]
            file_contents += self._formatNumber(cuota / base_imponible * 100 if base_imponible else 0, 3,2) # tipo % codes - [2,5,8,11,14,17]
            file_contents += self._formatNumber(cuota, 15,2) # cuota X % -- codes [3,6,9,12,15,18]
        
        
        # -- Adquisiciones Intracomunitarias - codes [19,20]
        
        file_contents += self._formatNumber(lines.get("[19]"), 15,2) ## base imponible
        file_contents += self._formatNumber(lines.get("[20]"), 15,2) ## cuota
        
        # -- Total Cuota Devengada - code [21]
        
        file_contents += self._formatNumber(report.total_devengado, 15,2) ## cuota
        
        ## IVA deducible 
        
        # -- Por Cuotas soportadas ... - codes [22~25]
        # -- Por Cuotas satisfechas en ... - codes [26~29]
        # -- En adquisiciones intracomunitarias de bienes ... - codes [30~33]
        
        for i in range(22,34):
            file_contents += self._formatNumber(lines.get("[%s]" % i), 15,2)
            
        # -- 
        
        file_contents += self._formatNumber(lines.get("[34]"), 15,2) # Compesaciones Regimen Especial AG y P
        file_contents += self._formatNumber(lines.get("[35]"), 15,2) # Regularización Inversiones
        file_contents += self._formatNumber(lines.get("[36]"), 15,2) # Regularización Inversiones por aplicación del porcentage def de prorrata
            
        # -- Total a deducir
        
        file_contents += self._formatNumber(report.total_deducir, 15,2)
        
        ## Diferencia [21] - [37]
        file_contents += self._formatNumber(report.diferencia, 15,2) 
        
        ## Atribuible a la administracion ...
        
        file_contents += self._formatNumber(report.porcentaje_atribuible_estado, 3,2) ## TODO Navarra y País Vasco
        file_contents += self._formatNumber(report.atribuible_estado, 15,2) 
        
        
        file_contents += self._formatNumber(report.cuota_compensar, 15,2) ## [41]
        
        
        ## Entregas intracomunitarias [42], Exportaciones y operaciones asimiladas ... [43], Derecho a deucción [44]
        
        file_contents += self._formatNumber(lines.get("[42]"), 15,2)
        file_contents += self._formatNumber(lines.get("[43]"), 15,2)
        file_contents += self._formatNumber(lines.get("[44]"), 15,2)        
        
        ## Estado y Comunidades Forales 
        
        file_contents += self._formatNumber(report.regularizacion_anual, 15,2)
        
        file_contents += self._formatNumber(report.resultado_casilla_46, 15,2) ## [40] - [41]
        
        ## A deducir - autoliquidación complementaria .... pedir campo
        
        file_contents += self._formatNumber(report.previus_result if report.complementaria else 0, 15,2)
        file_contents += self._formatNumber(report.resultado_liquidacion, 15,2) ## [48]
        
        ## A compensar
        file_contents += self._formatNumber(report.compensar, 15,2) ## [49]
        
        ## Marca SIN ACTIVIDAD
        
        file_contents += self._formatBoolean( report.sin_actividad , yes='1', no='2') #
        
        assert len(file_contents) == 822 - 72, _("The vat records must be 749 characters long and are %s") % len(file_contents)
        return file_contents

    def _get_formated_last_info(self, report):
        
        file_contents = ''

        ## devolucion (6)
        
        file_contents += self._formatNumber(report.devolver,15,2) ## devolucion [50]

        ccc = ""        
        if report.cuenta_devolucion_id and report.devolver:
            ccc = report.cuenta_devolucion_id.acc_number.replace("-","").replace(" ","")
            if not (len(ccc) == 20 and ccc.isdigit()):
                raise osv.except_osv(_('Warning'), _("CCC de devolución no válida \n%s") % ccc)
            
        file_contents += self._formatString(ccc,20) ## no hay devolución

        """
        ## ingreso (7)
        
        859     1     Num     Ingreso (7) - Forma de pago
        860     17    N       Ingreso (7) - Importe [I]
        877     4     An      Ingreso (7) - Código cuenta cliente - Entidad
        881     4     An      Ingreso (7) - Código cuenta cliente - Oficina
        885     2     An      Ingreso (7) - Código cuenta cliente - DC
        887     10    An      Ingreso (7) - Código cuenta cliente - Número de cuenta
        """
        
        file_contents += self._formatString("0",1) ## NO SE USA ??? Forma de Pago - "0" No consta, "1" Efectivo,"2" Adeudo en cuenta, "3" Domiciliación
        file_contents += self._formatNumber(report.ingresar,15,2) ## devolucion [50] 
        
        ccc = ""        
        if report.cuenta_ingreso_id and report.ingresar:
            ccc = report.cuenta_ingreso_id.acc_number.replace("-","").replace(" ","")
            if not (len(ccc) == 20 and ccc.isdigit()):
                raise osv.except_osv(_('Warning'), _("CCC de ingreso no válido %s") % ccc)
            
        file_contents += self._formatString(ccc,20) ## no hay devolución
        

        """
        897     1     Num     Complementaria (8) Indicador Autoliquidación complementaria
        898     13    An      Complementaria (8) - no justificante declaración anterior
        """

        file_contents += self._formatBoolean(report.complementaria, yes='1', no='0') #
        file_contents += self._formatString(report.previous_number if report.complementaria else "" ,13)
        
        
        ## TODO -- hardcode por ahora ...
        """ Autorización Conjunta """
        file_contents += self._formatBoolean(False, yes='1', no=' ')
        file_contents += self._formatString(' ',1) ## 77 autodeclaracion del concurso .... -- ' ' , '1' o '2'
        
        
        file_contents += ' '*398    ## campo reservado
        
        ## firma (9)
        
        file_contents += self._formatString(report.company_id.city,16)       ## Localidad
        

        calculation_date = datetime.strptime(report.calculation_date,"%Y-%m-%d %H:%M:%S")
        file_contents += self._formatString(calculation_date.strftime("%d"),2)              ## fecha: Dia
        file_contents += self._formatString(_(calculation_date.strftime("%B")),10)          ## fecha: Mes
        file_contents += self._formatString(calculation_date.strftime("%Y"),4)              ## fecha: Anio
        
        file_contents += self._formatString("</T30301>",9)
        file_contents += "\r\n".encode("ascii")
        
#        print file_contents
        return file_contents
    

    def _export_boe_file(self, cr, uid, ids, report, model=None, context=None):
        """
        Action that exports the data into a BOE formated text file
        """
        if context is None:
            context = {}

        assert model , _("AEAT Model is necessary")

        file_contents = ''

        ##
        ## IDENTIFICACION (1) y DEVENGO (2)
        file_contents += self._get_formated_declaration(report)

        ##
        ## LIQUIDACIÓN (3) y COMPENSACION(4)

        file_contents += self._get_formated_vat(cr,uid,ids,report)

        ##
        ## DEVOLUCION (6), INGRESO (7), COMPLEMENTARIA (8) Y FIRMA (9)
        file_contents += self._get_formated_last_info(report)

        assert len(file_contents) == 1353, _("The 303 report must be 1353 characters long and are %s") % len(file_contents)
        

        ##
        ## Generate the file and save as attachment
        file = base64.encodestring(file_contents)

        file_name = _("%s_report_%s.txt") % (model, time.strftime(_("%Y-%m-%d")))
        self.pool.get("ir.attachment").create(cr, uid, {
            "name" : file_name,
            "datas" : file,
            "datas_fname" : file_name,
            "res_model" : "l10n.es.aeat.mod%s.report" % model,
            "res_id" : ids and ids[0]
        }, context=context)

l10n_es_aeat_mod303_export_to_boe()
