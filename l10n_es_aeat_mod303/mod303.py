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


import re
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta


from osv import osv, fields
from tools.translate import _
from account.report.account_tax_report import tax_report 


class l10n_es_aeat_mod303_report(osv.osv):

    _inherit = "l10n.es.aeat.report"
    _name = "l10n.es.aeat.mod303.report"
    _description = "AEAT 303 Report"
    _rec_name = "number"

    def button_calculate(self, cr, uid, ids, context=None):
        if not context:
            context = {}

        self.action_confirm(cr, uid, ids, context)

        return True

    def button_recalculate(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        self.action_confirm(cr, uid, ids, context)

        return True

    def button_export(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        export_obj = self.pool.get("l10n.es.aeat.mod303.export_to_boe")
        export_obj._export_boe_file(cr, uid, ids, self.browse(cr, uid, ids and ids[0]),'303')

        return True

    
    _columns = {
                
        'period': fields.selection([
            ('1T','First quarter'),('2T','Second quarter'),('3T','Third quarter'),
            ('4T','Fourth quarter'),('01','January'),('02','February'),('03','March'),('04','April'),
            ('05','May'),('06','June'),('07','July'),('08','August'),('09','September'),('10','October'),
            ('11','November'),('12','December')
            ], 'Periodo',states={'done':[('readonly',True)]}),
        'devolucion_mensual' : fields.boolean("Devolución Mensual",help="Inscrito en el Registro de Devolución Mensual",states={'done':[('readonly',True)]}),
        'complementaria' : fields.boolean("Autoliquidación Complementaria",help="Autoliquidación Complementaria",states={'done':[('readonly',True)]}),                
        'contact_name': fields.char("Full Name", size=40),
        'total_devengado' : fields.float("IVA Devengado",readonly=True), ## 21
        'total_deducir' : fields.float("IVA a Deducir",readonly=True), ## 37
        'diferencia' : fields.float("Diferencia",readonly=True,help="( IVA devengado - IVA deducible )"), ## 38
        'porcentaje_atribuible_estado' : fields.float("%", help="""Los sujetos pasivos que tributen conjuntamente a la Administración del Estado y a las Diputaciones Forales del País Vasco o a la ComunidadForal de Navarra, consignarán en esta casilla el porcentaje  del volumen de operaciones en territorio común. Los demás sujetos pasivos consignarán en esta casilla el 100%""",states={'done':[('readonly',True)]}), ## 39
        'atribuible_estado' : fields.float("Atribuible a la Administracion",readonly=True), ## 40
        'cuota_compensar' : fields.float("Cuotas a Compensar",help="Cuota a compensar de periodos anteriores",states={'done':[('readonly',True)]}), ## 41
        'regularizacion_anual' : fields.float("Regularización Anual",help="""En la última autoliquidación del  año (la del período 4T o mes 12) se hará constar, con el signo que  corresponda, el resultado de la regularización anual conforme disponen las Leyes por las que se aprueban el Concierto Económico entre el Estado y la Comunidad Autónoma del País  Vasco y el Convenio Económico entre el Estado y la Comunidad Foral de Navarra.""",states={'done':[('readonly',True)]}), ## 45
        'resultado_casilla_46' : fields.float("Resultado",help="""Atribuible a la admistracion [40] - Cuotas a compensar [41] + Regularización Anual [45]""",readonly=True), ## 46
        
        'previus_result' : fields.float("A Deducir",help="Resultado de la anterior o anteriores del mismo concepto, ejercicio y periodo",states={'done':[('readonly',True)]}), ## 47
        'resultado_liquidacion' : fields.float("Resultado Liquidación",readonly=True), ## 48
    
        'compensar' : fields.float("Compensar",states={'done':[('readonly',True)]}), ## 49
        
        "devolver" : fields.float("Devolver",states={'done':[('readonly',True)]}),
        "ingresar" : fields.float("Ingresar",states={'done':[('readonly',True)]}),
        
        'cuenta_devolucion_id' : fields.many2one("res.partner.bank","CCC Devolución",states={'done':[('readonly',True)]}),
        'cuenta_ingreso_id' : fields.many2one("res.partner.bank","CCC Ingreso",states={'done':[('readonly',True)]}),
        
        'sin_actividad' : fields.boolean("Sin Actividad",states={'done':[('readonly',True)]}),
        
        
#        'type': fields.selection([
#            ('C','Solicitud de compensación'),
#            ('D','Devolución'),
#            ('G','CC Tributaria-Ingreso'),
#            ('I','Ingreso'),
#            ('N','Sin Actividad'),
#            ('V','CC Tributaria-Devolución'),
#            ('U','Domicilación de CCC'),], 'Statement Type',
#            required=True),

    }
    _defaults = {
        'number' : lambda *a: '303',
        'porcentaje_atribuible_estado': lambda *a: 100,
        'cuota_compensar' : lambda *a: 0
    }


    def _get_period(self,cr,uid,ids,context=None):

        period_obj = self.pool.get("account.period")
        quarter_dict = {"1T" : 'first',
                        "2T" : 'second',
                        "3T" : 'third',
                        "4T" : 'fourth',
                        }
        account_period_id = []
        
        for mod303 in self.browse(cr, uid, ids, context):
            
            fecha_ini = False
            fecha_fin = False
        
            dec_year = mod303.fiscalyear_id.date_start.split('-')[0]
            
            mod = mod303.period
    
            if mod >= '01' and mod <= '12':
                fecha_ini = datetime.strptime('%s-%s-01' % (dec_year, mod), '%Y-%m-%d')
                fecha_fin = fecha_ini + relativedelta(months=+1, days=-1)
                account_period_id = period_obj.search(cr,uid,[('date_start','=',fecha_ini),('date_stop','=',fecha_fin)])
                
            if mod in ('1T', '2T', '3T', '4T'):
                month = ( ( int(mod[0])-1 ) * 3 ) + 1
                fecha_ini = datetime.strptime('%s-%s-01' % (dec_year, month), '%Y-%m-%d')
                fecha_fin = fecha_ini + relativedelta(months=+3, days=-1)
            
                account_period_id = period_obj.search(cr,uid,[('date_start','=',fecha_ini),('date_stop','=',fecha_fin)])
                if not account_period_id:
                    account_period_id = period_obj.search(cr,uid,[('quarter','=',quarter_dict[mod])])
            if not account_period_id:
                raise osv.except_osv(_('El periodo seleccionado no coincide con los periodos del año fiscal:'), dec_year)
            
        return account_period_id
                

    def _get_report_lines(self, cr, uid, ids, context=None):
        """get report lines"""
        
        
        dict_code_values = {}
        for i in range(1,51):
            dict_code_values["[%.2d]" % i] = 0
        
        for mod303 in self.browse(cr, uid, ids, context):
            
            generate_line = tax_report(cr,uid,"account.vat.declaration")
            generate_line.period_ids = self._get_period(cr,uid,[mod303.id],context)
            generate_line.display_detail = False
            lines = generate_line._get_lines( 'invoices', mod303.company_id.id)
                
            ordered_lines = sorted(lines, key=lambda k: k['code'])
            
            
            for code in dict_code_values.keys():
                for line in ordered_lines:
                    if code == line["code"]:
                        dict_code_values[code] += line["tax_amount"]
            
        return dict_code_values
    
   
        

    def action_confirm(self, cr, uid, ids, context=None):
        """set to done the report and check its records"""
        if context is None: context = {}
        for mod303 in self.browse(cr, uid, ids, context):
            report_lines = self._get_report_lines(cr, uid, ids, context)
            regularizacion_anual = mod303.regularizacion_anual if ( mod303.period == "4T" or mod303.period == "12" ) else 0
            total_devengado = report_lines.get("[21]")
            total_deducir = report_lines.get("[37]")
            atribuible_estado = (total_devengado - total_deducir) * mod303.porcentaje_atribuible_estado / 100 ## casilla 40
            casilla_46 = atribuible_estado - mod303.cuota_compensar + regularizacion_anual
            previus_result = mod303.previus_result if mod303.complementaria else 0
            resultado_liquidacion = casilla_46 - previus_result
            vals = {
                    'state': 'calculated',
                    'calculation_date':time.strftime('%Y-%m-%d'),
                    'total_devengado':total_devengado,
                    'total_deducir':total_deducir,
                    'diferencia': total_devengado - total_deducir,
                    'atribuible_estado' : atribuible_estado,
                    'resultado_casilla_46' : casilla_46,
                    'resultado_liquidacion' : resultado_liquidacion,
                    'compensar' : abs(resultado_liquidacion) if resultado_liquidacion < 0 and mod303.devolver == 0 else 0, 
                    'ingresar' : resultado_liquidacion if resultado_liquidacion > 0 else 0
                    }
            
            if mod303.regularizacion_anual > 0 and not ( mod303.period == "4T" and mod303.period == "12" ):
                self.log(cr,uid,mod303.id,_("El valor añadido para la regularizacion anual no se ha tendio en cuenta por no ser un periodo de cierre (12 o 4T)"),context)
            
            self.write(cr, uid, mod303.id, vals)

        return True
    
    def confirm(self, cr, uid, ids, context=None):
        """set to done the report and check its records"""
        
        msg_validation = ""
        for mod303 in self.browse(cr,uid,ids,context):
            
            if mod303.ingresar > 0 and not mod303.cuenta_ingreso_id:
                msg_validation = _('Seleccione una cuenta para ingresar el importe')
            if mod303.devolver > 0 and not mod303.cuenta_devolucion_id:
                msg_validation = _('Seleccione una cuenta para realizar la devolución')
            if mod303.resultado_liquidacion == 0 and not mod303.sin_actividad:
                msg_validation = _("No hay actividad en el periodo seleccionado, marque la casilla correspondinte")
        
        
        if msg_validation:
            raise osv.except_osv("",msg_validation)
        
        self.write(cr, uid, ids, {'state': 'done'})
        
        return True
        
    def cancel(self, cr, uid, ids, context=None):
        """set to done the report and check its records"""
        self.write(cr, uid, ids, {'state': 'canceled'})

        return True    

l10n_es_aeat_mod303_report()
