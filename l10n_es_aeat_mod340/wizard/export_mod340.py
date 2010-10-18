# -*- encoding: utf-8 -*-
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

import pooler
import wizard
import base64
import mx.DateTime
from mx.DateTime import now
import netsvc
logger = netsvc.Logger()

mod340_form = """<?xml version="1.0"?>
<form string="Model 340 export">
    <label string="Do you want to export Model 340" />
</form>"""

mod340_fields = {}

export_form = """<?xml version="1.0"?>
<form string="Payment order export">
    <field name="mod340" filename="pay_fname"/>
    <field name="mod340_fname" invisible="1"/>
    <field name="note" colspan="4" nolabel="1"/>
</form>"""

export_fields = {
    'mod340' : {
        'string':'Modelo 340 file',
        'type':'binary',
        'required': False,
        'readonly':True,
    },
    'mod340_fname': {'string':'File name', 'type':'char', 'size':64},
    'note' : {'string':'Log', 'type':'text'},
}


def digitos_cc(cc_in):
    """Quita los espacios en blanco del número de C.C. (por ej. los que pone el módulo l10n_ES_partner)"""
    cc = ""
    for i in cc_in:
        try:
            int(i)
            cc += i
        except ValueError:
            pass
    return cc


def conv_ascii(text):
    """Convierte vocales accentuadas, ñ y ç a sus caracteres equivalentes ASCII"""
    old_chars = ['á','é','í','ó','ú','à','è','ì','ò','ù','ä','ë','ï','ö','ü','â','ê','î','ô','û','Á','É','Í','Ú','Ó','À','È','Ì','Ò','Ù','Ä','Ë','Ï','Ö','Ü','Â','Ê','Î','Ô','Û','ñ','Ñ','ç','Ç','ª','º']
    new_chars = ['a','e','i','o','u','a','e','i','o','u','a','e','i','o','u','a','e','i','o','u','A','E','I','O','U','A','E','I','O','U','A','E','I','O','U','A','E','I','O','U','n','N','c','C','a','o']
    for old, new in zip(old_chars, new_chars):
        text = text.replace(unicode(old,'UTF-8'), new)
    return text

def _formatearCadena(cadena, longitud,caracter,derecha):
    #funcion para rellenar la cadena para la aeat
    if cadena:
        posiciones = longitud - len(cadena)
        if derecha == True:
            cadena += posiciones * caracter
        else:
            cadena = (posiciones * caracter) + cadena 
    else:
        cadena = longitud*' '
    #devuelve la cadena en mayusculas
    return cadena.upper()
    
def _formatearDecimal(numero, enteros, decimales,incluir_signo):
    #funcion para formatear los numeros para la aeat
    if numero:
        cadena = str(numero)
    else:
        numero = 0
        cadena = '0.00'

    separacion = cadena.partition('.')

    if numero >= 0 and incluir_signo == True:
        signo = ' '
    elif numero < 0 and incluir_signo == True:
        signo = 'N'
    else:
        signo = ''

    parteEntera = _formatearCadena(separacion[0],enteros,'0',False)
    parteDecimal = _formatearCadena(separacion[2],decimales,'0',True)

    return signo + parteEntera + parteDecimal

class Log(Exception):
    def __init__(self):
        self.content = ""
        self.error = False
    def add(self, s, error=True):
        self.content = self.content + s
        if error:
            self.error = error
    def __call__(self):
        return self.content
    def __str__(self):
        return self.content


def _create_mod340_file(self, cr, uid, data, context):

    #pediente de solucionar el tema de las secuencia de la declaracion
    def _number_ident(fiscalyear,period,sequence):
        return '340' + fiscalyear + period + '0001'

    def _cabecera_modelo_340(self):
        #Datos Compañia
        company_obj = mod340.company_id

        if _formatearCadena(mod340.type,1,' ',True) == ' ':
            tipo_declaracion = [' ',' ']
        elif  _formatearCadena(mod340.type,1,' ',True) == 'C':
            tipo_declaracion = ['C',' ']
        elif  _formatearCadena(mod340.type,1,' ',True) == 'S':
            tipo_declaracion = [' ','S']

        texto = '1'
        texto += '340'
        texto += str(mod340.fiscalyear)
        texto += _formatearCadena(company_obj.partner_id.vat[2:len(company_obj.partner_id.vat)], 9, ' ', True)
        texto += _formatearCadena(company_obj.name,40,' ',True)
        texto += _formatearCadena(mod340.type_support,1,' ',True)
        texto += _formatearCadena(mod340.phone_contact,9,' ',True)
        texto += _formatearCadena(mod340.name_contact,40,' ',True)
        #texto += _formatearCadena('',13,' ',True) #demomento blanco pendiente
        texto += _number_ident(str(mod340.fiscalyear),_formatearCadena(mod340.period,2,' ',True),'')
        texto += tipo_declaracion[0] #Declaracion complementaria
        texto += tipo_declaracion[1] #Declaracion Sustitutiva
        #texto += _formatearCadena('',13,' ',True) #demomento blanco falta crear campo iden declaracion anterior
        texto += 13*'0' #demomento blanco falta crear campo iden declaracion anterior
        texto += _formatearCadena(mod340.period,2,' ',True)
        texto += _formatearDecimal(mod340.number_records,9,0,False)
        texto += _formatearDecimal(mod340.total_taxable,15,2,True)
        texto += _formatearDecimal(mod340.total_sharetax,15,2,True)
        texto += _formatearDecimal(mod340.total,15,2,True)
        texto += 190*' '
        texto += _formatearCadena(mod340.vat_representative,9,' ',True)
        texto += 101*' '
        texto += '\r\n'
        #texto += _formatearCadena(mod340.name_surname,40,' ',True)
        #logger.notifyChannel('cabecera presentador: ',netsvc.LOG_INFO, texto)
        return texto

    def _line_issued_modelo_340(self,linea):
        #Datos Compañia
        company_obj = mod340.company_id

        texto = '2'
        texto += '340'
        texto += str(mod340.fiscalyear)
        texto += _formatearCadena(company_obj.partner_id.vat[2:len(company_obj.partner_id.vat)], 9, ' ', True)
        texto += _formatearCadena(linea['vat_declared'],9, ' ', True)
        texto += _formatearCadena(linea['vat_representative'],9, ' ', True)
        texto += _formatearCadena(linea['partner_name'],40, ' ', True)
        texto += _formatearCadena(linea['cod_country'],2, ' ', True)
        texto += _formatearCadena(linea['key_country'],1, ' ', True)
        texto += _formatearCadena(linea['vat_country'],20, ' ', True)
        texto += _formatearCadena(linea['key_book'],1, ' ', True)
        texto += _formatearCadena(linea['key_operation'],1, ' ', True)
        texto += linea['invoice_date'].replace('-','')
        texto += linea['operation_date'].replace('-','')
        texto += _formatearDecimal(linea['rate'],3,2,False)
        texto += _formatearDecimal(linea['taxable'],11,2,True)
        texto += _formatearDecimal(linea['share_tax'],11,2,True)
        texto += _formatearDecimal(linea['total'],11,2,True)
        texto += _formatearDecimal(linea['taxable_cost'],11,2,True)
        texto += _formatearCadena(linea['number'],40, ' ', True)
        texto += _formatearCadena(linea['number_amendment'],18, ' ', True)
        texto += _formatearDecimal(linea['number_invoices'],8,0,False)
        texto += _formatearDecimal(linea['number_records'],2,0,False)
        texto += _formatearCadena(linea['iterval_ini'],40, ' ', True)
        texto += _formatearCadena(linea['iterval_end'],40, ' ', True)
        texto += _formatearCadena(linea['invoice_corrected'],40, ' ', True)
        texto += _formatearDecimal(linea['charge'], 3, 2, False)
        texto += _formatearDecimal(linea['share_charge'],11, 2, True)
        texto += 116*' ' + '\r\n'
        #texto += '\r\n'

        return texto    

    txt_mod340 = ''
    log = Log()
    try:
        pool = pooler.get_pool(cr.dbname)
        mod340 = pool.get('l10n.es.aeat.mod340').browse(cr, uid, data['id'], context)
        contador = 1
        lines_issued = []
        #antes hay que generar las lineas
        txt_mod340 += _cabecera_modelo_340(self)

        #Generamos registros correspodientes a facturas expedidas
        #llenamos el diccionario
        for l in mod340.issued:
            lines_issued.append({
                'vat_declared' : l.vat_declared,
                'vat_representative' : l.vat_representative,
                'partner_name' : l.partner_name,
                'cod_country' : l.cod_country,
                'key_country' : l.key_country,
                'vat_country' : l.vat_country,
                'key_book' : l.key_book,
                'key_operation' : l.key_operation,
                'invoice_date' : l.invoice_date,
                'operation_date' : l.operation_date,
                'rate' : l.rate,
                'taxable' : l.taxable,
                'share_tax' : l.share_tax,
                'total' : l.total,
                'taxable_cost' : l.taxable_cost,
                'number' : l.number,
                #'number_amendment' : l.number_amendment,
                'number_amendment' : str(contador),  #demomento un contador hasta que vea como hacerlo bien
                #'number_invoices' :  l.number_invoices,
                'number_invoices' :  '1',
                #'number_records' :  l.number_records,
                'number_records' :  '1',
                'iterval_ini' :  l.iterval_ini,
                'iterval_end' :  l.iterval_end,
                'invoice_corrected' :  l.invoice_corrected,
                'charge' :  l.charge,
                'share_charge' :  l.share_charge,
            })
            contador = contador + 1
        for line_issued in lines_issued:
            txt_mod340 += _line_issued_modelo_340(self,line_issued)

    except Log:
        return {'note':log(), 'reference':mod340.id, 'mod340':False, 'state':'failed'}
    else:
        file = base64.encodestring(txt_mod340)
        #fname = (_('modelo340') + '_' + orden.mode.tipo + '_' + orden.reference + '.txt').replace('/','-')
        fname = (_('modelo340') + '_' + '.txt').replace('/','-')
        pool.get('ir.attachment').create(cr, uid, {
            #'name': _('Modelo340 ') + orden.mode.tipo + ' ' + orden.reference,
            'name': _('Modelo340 ') ,#+ orden.mode.tipo + ' ' + orden.reference,
            'datas': file,
            'datas_fname': fname,
            'res_model': 'l10n.es.aeat.mod340',
            'res_id': mod340.id,
            }, context=context)
        #log.add(_("Successfully Exported\n\nSummary:\n Total amount paid: %.2f\n Total Number of Payments: %d\n") % (-orden.total, num_recibos))
        pool.get('l10n.es.aeat.mod340').set_done(cr,uid,mod340.id,context)

        return {'note':log(), 'reference':mod340.id, 'mod340':file, 'mod340_fname':fname, 'state':'succeeded'}

class wizard_mod340_file(wizard.interface):
    states = {
        'init' : {
            'actions' : [],
            'result' : {'type' : 'form',
                        'arch' : mod340_form,
                        'fields' : mod340_fields,
                        'state' : [('end', 'Cancel'),('export', 'Export','gtk-ok') ]}
        },
        'export': {
            'actions' : [_create_mod340_file],
            'result' : {'type' : 'form',
                        'arch' : export_form,
                        'fields' : export_fields,
                        'state' : [('end', 'Ok','gtk-ok') ]}
        }

    }
wizard_mod340_file('export_mod340_file')
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

