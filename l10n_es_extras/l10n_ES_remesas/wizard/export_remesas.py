# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2006 ACYSOS S.L.. (http://acysos.com) All Rights Reserved.
#    Pedro Tarrafeta <pedro@acysos.com>
#
# Corregido para instalación TinyERP estándar 4.2.0: Zikzakmedia S.L. 2008
#   Jordi Esteve <jesteve@zikzakmedia.com>
#
# Añadidas cuentas de remesas y tipos de pago. 2008
#    Pablo Rocandio <salbet@gmail.com>
#
# Corregido para instalación OpenERP 5.0.0 sobre account_payment_extension: Zikzakmedia S.L. 2009
#   Jordi Esteve <jesteve@zikzakmedia.com>
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
from osv import osv
import time
import mx.DateTime
from mx.DateTime import RelativeDateTime, now, DateTime, localtime

export_form = """<?xml version="1.0"?>
<form string="Payment Export">
   <field name="pay"/>
   <field name="note" colspan="4" nolabel="1"/>
   </form>"""

export_fields = {
    'pay' : {
        'string':'Export File',
        'type':'binary',
        'required': False,
        'readonly':True,
    },
    'note' : {'string':'Log','type':'text'},
}


def digitos_cc(cc_in):
    "Quita los espacios en blanco del número de C.C. (por ej. los que pone el módulo digito_control_es)"
    cc = ""
    for i in cc_in:
        try:
            int(i)
            cc += i
        except ValueError:
            pass
    return cc


def conv_ascii(text):
    "Convierte vocales accentuadas, ñ y ç a sus caracteres equivalentes ASCII"
    old_chars = ['á','é','í','ó','ú','à','è','ì','ò','ù','ä','ë','ï','ö','ü','â','ê','î','ô','û','Á','É','Í','Ú','Ó','À','È','Ì','Ò','Ù','Ä','Ë','Ï','Ö','Ü','Â','Ê','Î','Ô','Û','ñ','Ñ','ç','Ç']
    new_chars = ['a','e','i','o','u','a','e','i','o','u','a','e','i','o','u','a','e','i','o','u','A','E','I','O','U','A','E','I','O','U','A','E','I','O','U','A','E','I','O','U','n','N','c','C']
    for old, new in zip(old_chars, new_chars):
        text = text.replace(old, new)
    return text


class Log:
    def __init__(self):
        self.content= ""
        self.error= False
    def add(self,s,error=True):
        self.content= self.content + s
        if error:
            self.error= error
    def __call__(self):
        return self.content

def _create_remesa(self,cr,uid,data,context):

    def _cabecera_presentador_19(self):
        texto = '5180'
        texto += (orden.mode.bank_id.partner_id.vat[2:] + orden.mode.sufijo).zfill(12)
        date_now = now().strftime('%d%m%y')
        texto += date_now
        texto += 6*' '
        texto += orden.mode.nombre.ljust(40)
        texto += 20*' '
        texto += cc[0:8]
        texto += 66*' '
        texto += '\r\n'
        #logger.notifyChannel('cabecera presentador',netsvc.LOG_INFO, texto)
        return texto

    def _cabecera_ordenante_19(self):
        texto = '5380'
        texto += (orden.mode.bank_id.partner_id.vat[2:] + orden.mode.sufijo).zfill(12)
        date_now = now().strftime('%d%m%y')
        texto += date_now
        if not orden.date_planned:
            raise osv.except_osv('Error del usuario', 'No se ha definido una fecha fija de cargo')
        date_cargo = mx.DateTime.strptime(orden.date_planned,'%Y-%m-%d')
        texto += str(date_cargo.strftime('%d%m%y'))
        texto += orden.mode.nombre.ljust(40)
        texto += cc[0:20]
        texto += 8*' '
        texto += '01'
        texto += 64*' '
        texto += '\r\n'
        return texto

    def _individual_obligatorio_19(self, recibo):
        # Comprobamos que exista número de C.C. y que tenga 20 dígitos
        if type(recibo.bank_id.acc_number) != str:
            raise osv.except_osv('Error del usuario', 'El número de C.C. del cliente %s no existe.' % recibo.partner_id.name)
        ccc = digitos_cc(recibo.bank_id.acc_number)
        if len(ccc) != 20:
            raise osv.except_osv('Error del usuario', 'El número de C.C. del cliente %s no tiene 20 dígitos.' % recibo.partner_id.name)

        texto = '5680'
        texto += (orden.mode.bank_id.partner_id.vat[2:] + orden.mode.sufijo).zfill(12)
        texto += recibo.name.__str__().zfill(12)
        nombre = conv_ascii(recibo.partner_id.name).decode('ascii', 'ignore')
        texto += nombre[0:40].ljust(40)
        texto += ccc.__str__()[0:20].zfill(20)
        importe = int(round(recibo.amount*100,0))
        texto += importe.__str__().zfill(10)
        texto += 16*' '
        concepto = ''
        if recibo.communication:
            concepto += recibo.communication
        if recibo.communication2:
            concepto += ' '+recibo.communication2
        texto += conv_ascii(concepto).decode('ascii', 'ignore')[0:48].ljust(48)
        # Esto es lo convencional, descripción de 40 caracteres, pero se puede aprovechar los 8 espacios en blanco finales
        #texto += conv_ascii(concepto).decode('ascii', 'ignore')[0:40].ljust(40)
        #texto += 8*' '
        texto += '\r\n'
        logger.notifyChannel('Individual obligatorio',netsvc.LOG_INFO, texto)
        return texto

    def _total_ordenante_19(self):
        texto = '5880'
        texto += (orden.mode.bank_id.partner_id.vat[2:] + orden.mode.sufijo).zfill(12)
        texto += 72*' '
        totalordenante = int(round(-orden.total * 100,0))
        texto += totalordenante.__str__().zfill(10)
        texto += 6*' '
        ndomic = num_recibos
        #logger.notifyChannel('Numero de recibos tot',netsvc.LOG_INFO, ndomic.__str__())
        texto += ndomic.__str__().zfill(10)
        texto += (ndomic + 2).__str__().zfill(10)
        texto += 38*' '
        texto += '\r\n'
        return texto

    def _total_general_19(self):
        texto = '5980'
        texto += (orden.mode.bank_id.partner_id.vat[2:] + orden.mode.sufijo).zfill(12)
        texto += 52*' '
        texto += '0001'
        texto += 16*' '
        totalremesa = int(round(-orden.total * 100,0))
        texto += totalremesa.__str__().zfill(10)
        texto += 6*' '
        ndomic = num_recibos
        #logger.notifyChannel('Numero de recibos tot',netsvc.LOG_INFO, ndomic.__str__())
        texto += ndomic.__str__().zfill(10)
        texto += (ndomic + 4).__str__().zfill(10)
        texto += 38*' '
        texto += '\r\n'
        return texto
        texto += '\r\n'
        return texto

    def _cabecera_presentador_58(self):
        texto = '5170'
        texto += (orden.mode.bank_id.partner_id.vat[2:] + orden.mode.sufijo).zfill(12)
        date_now = now().strftime('%d%m%y')
        texto += date_now
        texto += 6*' '
        texto += orden.mode.nombre.ljust(40)
        texto += 20*' '
        texto += cc[0:8]
        texto += 66*' '
        texto += '\n'
        #logger.notifyChannel('cabecera presentador',netsvc.LOG_INFO, texto)
        return texto

    def _cabecera_ordenante_58(self):
        texto = '5370'
        texto += (orden.mode.bank_id.partner_id.vat[2:] + orden.mode.sufijo).zfill(12)
        date_now = now().strftime('%d%m%y')
        texto += date_now
        texto += 6*' '
        texto += orden.mode.nombre.ljust(40)
        texto += cc[0:20]
        texto += 8*' '
        texto += '06'
        texto += 52*' '
        # Codigo INE de la plaza... en blanco...
        texto += 9*' '
        texto += 3*' '
        texto += '\n'
        return texto

    def _individual_obligatorio_58(self, recibo):
        # Comprobamos que exista número de C.C. y que tenga 20 dígitos
        if type(recibo.bank_id.acc_number) != str:
            raise osv.except_osv('Error del usuario', 'El número de C.C. del cliente %s no existe.' % recibo.partner_id.name)
        ccc = digitos_cc(recibo.bank_id.acc_number)
        if len(ccc) != 20:
            raise osv.except_osv('Error del usuario', 'El número de C.C. del cliente %s no tiene 20 dígitos.' % recibo.partner_id.name)

        texto = '5670'
        texto += (orden.mode.bank_id.partner_id.vat[2:] + orden.mode.sufijo).zfill(12)
        texto += recibo.name.__str__().zfill(12)
        nombre = conv_ascii(recibo.partner_id.name).decode('ascii', 'ignore')
        texto += nombre[0:40].ljust(40)
        texto += ccc.__str__()[0:20].zfill(20)
        importe = int(round(recibo.amount*100,0))
        texto += importe.__str__().zfill(10)
        texto += 16*' '
        concepto = ''
        if recibo.communication:
            concepto += recibo.communication
        if recibo.communication2:
            concepto += ' '+recibo.communication2
        texto += conv_ascii(concepto).__str__()[0:40].ljust(40)
        if recibo.date:
            texto += recibo.date
        else:
            texto += recibo.ml_maturity_date
        texto += 2*' '
        texto += '\n'
        #logger.notifyChannel('Individual obligaotrio',netsvc.LOG_INFO, texto)
        return texto

    def _registro_obligatorio_domicilio_58(self, recibo):
        texto = '5676'
        texto += (orden.mode.bank_id.partner_id.vat[2:] + orden.mode.sufijo).zfill(12)
        texto += recibo.name.__str__().zfill(12)
        texto += conv_ascii(recibo.partner_id.name).ljust(40)
        texto += recibo.bank_id.acc_number.__str__()[0:20].zfill(20)
        importe = int(recibo.amount*100)
        texto += importe.__str__().zfill(10)
        texto += 16*' '
        concepto = ''
        if recibo.communication:
            concepto += recibo.communication
        if recibo.communication2:
            concepto += ' '+recibo.communication2
        texto += conv_ascii(concepto).__str__()[0:40].ljust(40)
        if recibo.date:
            texto += recibo.date
        else:
            texto += recibo.ml_maturity_date
        texto += '  '
        texto += '\n'
        #logger.notifyChannel('Individual obligaotrio',netsvc.LOG_INFO, texto)
        return texto

    def _total_ordenante_58(self):
        texto = '5870'
        texto += (orden.mode.bank_id.partner_id.vat[2:] + orden.mode.sufijo).zfill(12)
        texto += 72*' '
        totalordenante = int(-orden.total * 100)
        texto += totalordenante.__str__().zfill(10)
        texto += 6*' '
        ndomic = num_recibos
        #logger.notifyChannel('Numero de recibos tot',netsvc.LOG_INFO, ndomic.__str__())
        texto += ndomic.__str__().zfill(10)
        texto += (ndomic + 2).__str__().zfill(10)
        texto += 38*' '
        texto += '\n'
        return texto

    def _total_general_58(self):
        texto = '5970'
        texto += (orden.mode.bank_id.partner_id.vat[2:] + orden.mode.sufijo).zfill(12)
        texto += 52*' '
        texto += '0001'
        texto += 16*' '
        totalremesa = int(round(-orden.total * 100,0))
        texto += totalremesa.__str__().zfill(10)
        texto += 6*' '
        ndomic = num_recibos
        #logger.notifyChannel('Numero de recibos tot',netsvc.LOG_INFO, ndomic.__str__())
        texto += ndomic.__str__().zfill(10)
        texto += (ndomic + 4).__str__().zfill(10)
        texto += 38*' '
        texto += '\n'
        return texto

    txt_remesa = ''
    num_recibos = 0
    log=''
    log=Log()

    pool = pooler.get_pool(cr.dbname)
    orden = pool.get('payment.order').browse(cr, uid, data['id'], context)
    if not orden.line_ids:
        return {'note':'Wizard can not generate export file: there are no payment lines.', 'reference': orden.id, 'pay': False, 'state':'failed' }

    # Comprobamos que exista número de C.C. y que tenga 20 dígitos
    if not orden.mode.bank_id:
        raise osv.except_osv('Error del usuario', 'No se ha definido el C.C. de la compañía %s.' % rem.cuenta_id.nombre)
    cc = digitos_cc(orden.mode.bank_id.acc_number)
    if len(cc) != 20:
        raise osv.except_osv('Error del usuario', 'El número de C.C. de la compañía %s no tiene 20 dígitos.' % rem.cuenta_id.partner_id.name)
    # Comprobamos que exista el CIF de la compañía asociada al C.C. del modo de pago
    if not orden.mode.bank_id.partner_id.vat:
        raise osv.except_osv('Error del usuario', 'No se ha definido el CIF de la compañía asociada al C.C. del modo de pago.')

    if orden.mode.tipo == 'csb_19':
        txt_remesa += _cabecera_presentador_19(self)
        txt_remesa += _cabecera_ordenante_19(self)

        for recibo in orden.line_ids:
            txt_remesa += _individual_obligatorio_19(self, recibo)
            num_recibos = num_recibos + 1
            print recibo

        txt_remesa += _total_ordenante_19(self)
        txt_remesa += _total_general_19(self)
        #self.write(cr, uid, ids, {'texto':txt_remesa, 'fichero':base64.encodestring(txt_remesa)})
        #logger.notifyChannel('remesas texto',netsvc.LOG_INFO, '\r\n' + txt_remesa)

    elif orden.mode.tipo == 'csb_58':
        txt_remesa += _cabecera_presentador_58(self)
        txt_remesa += _cabecera_ordenante_58(self)

        for recibo in orden.line_ids:
            txt_remesa += _individual_obligatorio_58(self, recibo)
            num_recibos = num_recibos + 1
            print recibo

        txt_remesa += _total_ordenante_58(self)
        txt_remesa += _total_general_58(self)
        #self.write(cr, uid, ids, {'texto':txt_remesa, 'fichero':base64.encodestring(txt_remesa)})
        #logger.notifyChannel('remesas texto',netsvc.LOG_INFO, '\r\n' + txt_remesa)

    try:
        txt_remesa = txt_remesa
    except Exception,e :
        log= log +'\n'+ str(e) + 'CORRUPTED FILE !\n'
        raise
    log.add("Successfully Exported\n--\nSummary:\n\nTotal amount paid : %.2f \nTotal Number of Payments : %d \n-- " %(-orden.total, num_recibos))
    return {'note':log(), 'reference': orden.id, 'pay': base64.encodestring(txt_remesa), 'state':'succeeded'}

    pool.get('payment.order').set_done(cr,uid,orden.id,context)
    return {'note':log(), 'reference': orden.id, 'pay': base64.encodestring(txt_remesa), 'state':'succeeded'}


def _log_create(self, cr, uid, data, context):
    pool = pooler.get_pool(cr.dbname)
    pool.get('account.pay').create(cr,uid,{
        'payment_order_id': data['form']['reference'],
        'note': data['form']['note'],
        'file': data['form']['pay'] and base64.encodestring(data['form']['pay'] or False),
        'state': data['form']['state'],
    })

    return {}

class wizard_export_remesas(wizard.interface):
    states = {
        'init' : {
            'actions' : [_create_remesa],
            'result' : {'type' : 'form',
                        'arch' : export_form,
                        'fields' : export_fields,
                        'state' : [('close', 'Ok','gtk-ok') ]}
        },
        'close': {
            'actions': [_log_create],
            'result': {'type': 'state', 'state':'end'}
        }

    }
wizard_export_remesas('export_remesas')
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

