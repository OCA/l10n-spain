# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 Acysos S.L. (http://acysos.com) All Rights Reserved.
#                       Ignacio Ibeas <ignacio@acysos.com>
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
from osv import fields,osv
from openerp import pooler
import wizard
import base64
from openerp.tools.translate import _
from converter import *

join_form = """<?xml version="1.0"?>
<form string="Export Correos File">
    <field name="certificate"/>
    <field name="color"/>
</form>"""

join_fields = {
    'certificate' : {'string':'Certificate letters', 'type':'boolean'},
    'color' : {'string':'Color letters', 'type':'boolean'},
}

export_form = """<?xml version="1.0"?>
<form string="Export Correos File">
    <field name="correos" filename="correos_fname"/>
    <field name="correos_fname" invisible="1"/>
    <field name="note" colspan="4" nolabel="1"/>
</form>"""

export_fields = {
    'correos' : {
        'string':'File name',
        'type':'binary',
        'required': False,
        'readonly':True,
    },
    'correos_fname': {'string':'File name', 'type':'char', 'size':64},
    'note' : {'string':'Log', 'type':'text'},
}

def _create_correos_file(self, cr, uid, data, context):
    txt_correos = ''
    try:
        if len(data['ids']) > 300:
            raise Log( _('User error:\n\n The Virtual Office of Correos only support 300 address. You have selected %s partners.') % (len(data['ids'])), True)
        else:
            pool = pooler.get_pool(cr.dbname)
            partner_obj = pool.get('res.partner')
            partners = partner_obj.browse(cr, uid, data['ids'], context)
            for partner in partners:
                address_id = partner_obj.address_get(cr, uid, [partner.id], ['delivery'])['delivery']
                if not address_id:
                    raise Log( _('User error:\n\n The partner %s hasn\'t address.') % (partner.name), True)
                address = pool.get('res.partner.address').browse(cr, uid, [address_id], context)[0]
                txt_correos += 48*" "+"\t"
                txt_correos += 48*" "+"\t"
                txt_correos += to_ascii(partner.name)[0:50].ljust(50)+"\t"
                txt_correos += 44*" "+"\t"
                if address.street: txt_correos += to_ascii(address.street)[0:50].ljust(50)+"\t"
                else: raise Log( _('User error:\n\n The partner %s hasn\'t street.') % (partner.name), True)
                if address.zip: txt_correos += to_ascii(address.zip)[0:10].ljust(10)+"\t"
                else: raise Log( _('User error:\n\n The partner %s hasn\'t zip.') % (partner.name), True)
                if address.city: txt_correos += to_ascii(address.city)[0:50].ljust(50)+"\t"
                else: raise Log( _('User error:\n\n The partner %s hasn\'t city.') % (partner.name), True)
                if address.state_id: txt_correos += to_ascii(address.state_id.name)[0:50].ljust(50)+"\t"
                else: raise Log( _('User error:\n\n The partner %s hasn\'t state.') % (partner.name), True)
                if address.country_id: txt_correos += to_ascii(address.country_id.code)[0:2].ljust(2)+"\t"
                else: raise Log( _('User error:\n\n The partner %s hasn\'t country.') % (partner.name), True)
                txt_correos += str(data['form']['color'])+"\t"
                txt_correos += str(data['form']['certificate'])+"\t"
                txt_correos += '\r\n'
    except Log, log:
        return {
            'note': log(),
            'correos': False,
            'state':'failed'
        }
    else:
        txt_correos = txt_correos.replace('\r\n','\n').replace('\n','\r\n')
        file = base64.encodestring(txt_correos)
        fname = 'export_correos.txt'
        log = _("Successfully Exported\n\nSummary::\n Number of exported partners: %d\n") % (len(partners))
        return {
            'note': log,
            'correos': file,
            'correos_fname': fname,
            'state': 'succeeded',
        }

class wizard_correos_file(wizard.interface):
    states = {
        'init' : {
            'actions' : [],
            'result' : {'type' : 'form',
                        'arch' : join_form,
                        'fields' : join_fields,
                        'state' : [('export', 'Ok','gtk-ok') ]}
        },
        'export': {
            'actions' : [_create_correos_file],
            'result' : {'type' : 'form',
                        'arch' : export_form,
                        'fields' : export_fields,
                        'state' : [('end', 'Ok','gtk-ok') ]}
        }
    }
wizard_correos_file('export_correos_file')