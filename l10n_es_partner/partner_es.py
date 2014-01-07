# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008 Spanish Localization Team
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2012-2014 Acysos S.L. (http://acysos.com) All Rights Reserved.
#                       Ignacio Ibeas <ignacio@acysos.com>
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

from osv import osv, fields
from tools.translate import _
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

def checkBankAccount(account):
    number = ""
    for i in account:
        if i.isdigit():
            number += i
    if len(number) != 20:
        return 'invalid-size'
    bank = number[0:4]
    office = number[4:8]
    dc = number[8:10]
    account = number[10:20]
    if dc != CalcCC(bank, office, account):
        return 'invalid-dc'
    return '%s %s %s %s' % (bank, office, dc, account)

def _pretty_iban(iban_str):
    "return iban_str in groups of four characters separated by a single space"
    res = []
    while iban_str:
        res.append(iban_str[:4])
        iban_str = iban_str[4:]
    return ' '.join(res)

class res_partner_bank(osv.osv):
    _inherit = 'res.partner.bank'
    _columns = {
        'acc_country_id': fields.many2one("res.country", 'Bank country', help="If the country of the bank is Spain, it validates the bank code. It only reads the digit characters of the bank code:\n- If the number of digits is 18, computes the two digits of control.\n- If the number of digits is 20, computes the two digits of control and ignores the current ones.\n- If the number of digits is different from 18 or 20, it leaves the bank code unaltered.\nThe result is shown in the '1234 5678 06 1234567890' format."),
    }

    def onchange_banco(self, cr, uid, ids, account, country_id, state, context=None):
        if account and country_id:
            country = self.pool.get('res.country').browse(cr, uid, country_id, context)
            if country.code.upper() in ('ES'):
                bank_obj = self.pool.get('res.bank')
                if state == 'bank':
                    number = checkBankAccount( account )
                    if number == 'invalid-size':
                        return { 'warning': { 'title': _('Warning'), 
                                 'message': _('Bank account should have 20 digits.') } }
                    if number == 'invalid-dc':
                        return { 'warning': { 'title': _('Warning'), 
                                     'message': _('Invalid bank account.') } }

                    bank_ids = bank_obj.search(cr, uid, 
                                               [('code','=',number[:4])], 
                                               context=context)
                    if bank_ids:
                        return {'value':{'acc_number': number, 
                                         'bank': bank_ids[0]}}
                    else:
                        return {'value':{'acc_number': number}}
                elif state =='iban':
                    partner_bank_obj = self.pool.get('res.partner.bank')
                    if partner_bank_obj.is_iban_valid(cr,uid,account,context):
                        number = _pretty_iban(account.replace(" ", ""))
                        
                        bank_ids = bank_obj.search(cr, uid, 
                                                   [('code','=',number[5:9])], 
                                                   context=context)
                        if bank_ids:
                            return {'value':{'acc_number': number, 
                                             'bank': bank_ids[0]}}
                        else:
                            return {'value':{'acc_number': number}}
                    else:
                       return { 'warning': { 'title': _('Warning'), 
                                'message': _('IBAN account is not valid') } } 
        return {'value':{}}

res_partner_bank()


class Bank(osv.osv):
    _inherit = 'res.bank'
    _columns = {
        'code': fields.char('Code', size=64),
        'lname': fields.char('Long name', size=128),
        'vat': fields.char('VAT code',size=32 ,help="Value Added Tax number"),
        'website': fields.char('Website',size=64),
        'code': fields.char('Code', size=64),
    }
Bank()


class res_partner(osv.osv):
    _inherit = 'res.partner'
    _columns = {
        'comercial': fields.char('Trade name', size=128, select=True), # Nombre Comercial del Partner
    }

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args=[]
        if not context:
            context={}

        partners = super(res_partner, self).name_search(cr, uid, name, args,
                                                    operator, context, limit)
        ids = [x[0] for x in partners]
        if name and len(ids) == 0:
            ids = self.search(cr, uid, [('comercial', operator, name)] + args,
                                                limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)
      

    def vat_change(self, cr, uid, ids, value, context=None):
        result = super(res_partner,self).vat_change(cr, uid, ids, value, context = context)
        if value:
            result['value']['vat'] = value.upper()
        return result

res_partner()


class l10n_es_partner_import_wizard(osv.osv_memory):
    _name = 'l10n.es.partner.import.wizard'
    _inherit = 'res.config.installer'

    def execute(self, cr, uid, ids, context=None):
        try:
            fp = tools.file_open(os.path.join('l10n_es_partner', 'data_banks.xml'))
        except IOError, e:
            return {}
        idref = {}
        tools.convert_xml_import(cr, 'l10n_es_partner', fp,  idref, 'init', noupdate=True)
        return {}
        
l10n_es_partner_import_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
