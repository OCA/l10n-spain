# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008 Spanish Localization Team
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
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

from osv import osv, fields
import tools
import os

def _CRC(cTexto):
    """Calculo el CRC de un número de 10 dígitos
    ajustados con ceros por la izquierda"""
    factor=(1,2,4,8,5,10,9,7,3,6)
    # Cálculo CRC
    nCRC=0
    for n in range(10):
        nCRC += int(cTexto[n])*factor[n]
    # Reducción del CRC a un dígito
    nValor=11 - nCRC%11
    if nValor==10: nValor=1
    elif nValor==11: nValor=0
    return nValor

def CalcCC(cBanco,cSucursal,cCuenta):
    """Cálculo del Código de Control Bancario"""
    cTexto="00%04d%04d" % (int(cBanco),int(cSucursal))
    DC1=_CRC(cTexto)
    cTexto="%010d" % long(cCuenta)
    DC2=_CRC(cTexto)
    return "%1d%1d" % (DC1,DC2)

class res_partner_bank(osv.osv):
    _inherit = 'res.partner.bank'
    _columns = {
        'acc_country_id': fields.many2one("res.country", 'Bank country', help="If the country of the bank is Spain, it validates the bank code. It only reads the digit characters of the bank code:\n- If the number of digits is 18, computes the two digits of control.\n- If the number of digits is 20, computes the two digits of control and ignores the current ones.\n- If the number of digits is different from 18 or 20, it leaves the bank code unaltered.\nThe result is shown in the '1234 5678 06 1234567890' format."),
        }
    def onchange_banco(self, cr, uid, ids, account, country_id):
        # No se por qué motivo, al añadir un nuevo banco, en ocasiones
        # la función onchange_banco se ejecuta con el valor account=False
        # dando el error: TypeError: 'bool' object is not iterable
        # El problema se resuelve con las tres siguientes líneas

        if type(account) <> str or type(country_id) <> int:
            #print "¿Por qué account es <type 'bool'>?"
            return {'value':{}}
        country = self.pool.get('res.country').browse(cr, uid, country_id)
        if country.code.upper() in ('ES', 'CT'):
            number = ""
            for i in account:
                if i.isdigit():
                    number += i
            if len(number) == 18:
                cuenta = number[8:18]
            elif len(number) == 20:
                cuenta = number[10:20]
            else:
                return {'value':{}}
            name = number[0:4]
            oficina = number[4:8]
            dc = CalcCC(name, oficina, cuenta)
            number = "%s %s %s %s" %(name, oficina, dc, cuenta)
            b = self.pool.get('res.bank')
            b_id = b.search(cr, uid, [('code','=',name)])
            if b_id:
                return {'value':{'acc_number': number, 'bank': b_id[0]}}
            else:
                return {'value':{'acc_number': number}}
        return {'value':{}}
res_partner_bank()


class Bank(osv.osv):
    _inherit = 'res.bank'
    _columns = {
        'lname': fields.char('Long name', size=128),
        'vat': fields.char('VAT code',size=32 ,help="Value Added Tax number"),
        'website': fields.char('Website',size=64),
    }
Bank()


class res_partner(osv.osv):
    _inherit = 'res.partner'
    _columns = {
        'comercial': fields.char('Trade name', size=128, select=True), # Nombre Comercial del Partner
    }
res_partner()


class l10n_es_partner_import_wizard(osv.osv_memory):
    _name = 'l10n.es.partner.import.wizard'

    def action_import(self, cr, uid, ids, context=None):
        try:
            fp = tools.file_open(os.path.join('l10n_ES_partner', 'data_banks.xml'))
        except IOError, e:
            return {}
        idref = {}
        tools.convert_xml_import(cr, 'l10n_ES_partner', fp,  idref, 'init', noupdate=True)
        return {}
l10n_es_partner_import_wizard()
