# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2009 Alejandro Sanchez (http://www.asr-oss.com) All Rights Reserved.
#                    Alejandro Sanchez <alejandro@asr-oss.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
###############################################################################

import wizard
import netsvc
import pooler
import string


field_duedate={
    'fromdate': {'string':'From Date', 'type':'date','required':True, },
    'todate': {'string':'To Date', 'type':'date','required':True, },
    }

import_issued_form = """<?xml version="1.0" encoding="utf-8"?>
<form string="Imports Invoices Issued">
   <!-- <label string="Do you want to import invoices issued for the selected dates?" />-->
    <field name="fromdate" />
    <field name="todate" />
</form>"""

def identNifDni(cadena):
    #identifica si es dni o Nif obteniento la primera parte de la cadena
    #asume que si es numero sera Dni si es letra Nif
    resultado = ""
    if cadena[0:1].isdigit() == True:
        resultado = "4"     
    else:
        resultado = "1"
    return resultado

def _importIssued(self, cr, uid, data, context):
    #recogida parametros
    pool = pooler.get_pool(cr.dbname)
    from_date_invoices = data['form']['fromdate']
    to_date_invoices = data['form']['todate']

    mod340_obj = pool.get('l10n.es.aeat.mod340').browse(cr, uid, data['id'],context=context)
    issued_obj = pool.get('l10n.es.aeat.mod340.issued')
    configura_obj = mod340_obj.config_id

    #prepara la where con los taxes que hemos configurado
    #solo para taxes_id ( emitdas )
    where_taxes = ""
    try:
      for tax in configura_obj.taxes_id:
        taxes_codes = tax.ref_tax_code_id
        if len(where_taxes) == 0:
                where_taxes = " and ( "
        else:
                where_taxes = where_taxes + " or"

        where_taxes = where_taxes + " t.tax_code_id = " + str(taxes_codes.id)
    except Exception:
        print "error"
    finally:
        #bloquea la insercion de registros no se han configurado taxes en config
        if where_taxes == "":
                where_taxes = "and t.tax_code_id = -1"
        else:
                where_taxes = where_taxes + " )"
    #recogida de datos
    cr.execute("""SELECT replace(p.vat,'ES',''),p.name,p.vat,
                  i.date_invoice,a.amount,t.base_amount,t.tax_amount,
                  i.amount_total,i.number, i.type
                FROM account_invoice_tax t 
	           left join account_invoice i on t.invoice_id = i.id
                   left join res_partner p on i.partner_id = p.id
                   left join account_tax a on t.tax_code_id = a.tax_code_id
                where i.state <> 'draft' and i.type =%s and i.date_invoice between %s and %s """  + where_taxes +
                """order by date_invoice""",('out_invoice',from_date_invoices,to_date_invoices))

    for resultado in cr.fetchall():
        vals = {
                'mod340_id' : mod340_obj.id,
                'vat_declared' : resultado[0],
                'vat_representative' : '',
                'partner_name': resultado[1],
                'cod_country' : resultado[2][0:2],
                'key_country' : identNifDni(resultado[0]),
                'key_book' : 'E',
                'key_operation' : 'J', 
                'invoice_date' : resultado[3],
                'operation_date' : resultado[3],
                'rate' : resultado[4] * 100,
                'taxable' : resultado[5],
                'share_tax' : resultado[6],
                'total' : resultado[7],
                'taxable_cost' : resultado[7],
                'number' : resultado[8],
        }
        issued_obj.create(cr, uid, vals)
    return {}

class wizard_issued(wizard.interface):
    states = {
        'init' : {
            'actions' : [],
            'result' : {'type' : 'form',
                    'arch' : import_issued_form,
                    'fields' : field_duedate,
                    'state' : [('end', 'Cancel'),('import', 'Import Issued') ]}
        },
        'import' : {
            'actions' : [],
            'result' : {'type' : 'action',
                    'action' : _importIssued,
                    'state' : 'end'}
        },
    }
wizard_issued('l10n_ES_aeat_mod340.wizard_issued')
