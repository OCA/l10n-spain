# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                    Jordi Esteve <jesteve@zikzakmedia.com>
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

import ir
import wizard
import pooler
from osv import osv, fields
import codecs
import tools

com_auto={'00':'', '01':'EK', '02':'CM', '03':'PV', '04':'AN', '05':'CL', '06':'EX', '07':'IB', '08':'CA', '09':'CL', '10':'EX', '11':'AN', '12':'PV', '13':'CM', '14':'AN', '15':'GA', '16':'CM', '17':'CA', '18':'AN', '19':'CM', '20':'EK', '21':'AN', '22':'AR', '23':'AN', '24':'CL', '25':'CA', '26':'LR', '27':'GA', '28':'MA', '29':'AN', '30':'MU', '31':'NA', '32':'GA', '33':'AS', '34':'CL', '35':'IC', '36':'GA', '37':'CL', '38':'IC', '39':'CB', '40':'CL', '41':'AN', '42':'CL', '43':'CA', '44':'AR', '45':'CM', '46':'PV', '47':'CL', '48':'EK', '49':'CL', '50':'AR', '51':'CE', '52':'ME'}

cpostal_end_form = '''<?xml version="1.0" encoding="utf-8"?>
<form string="Codis postals">
    <separator string="Resultat:" colspan="4"/>
    <label string="Se han asociado las Comunidades Autónomas a los códigos postales del Estado Español." colspan="4" align="0.0"/>
    <label string="Permite rellenar automáticamente el campo de Comunidad Autónoma del formulario de empresa y contacto a partir del código postal" colspan="4" align="0.0"/>
</form>'''

class l10n_ES_crea_cpostal_CA(wizard.interface):
    def _crea_cpostal(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        
        con = codecs.open(tools.config['addons_path']+'/l10n_ES_toponyms_CA/cpostal.csv','r','utf-8')
        for linea in con:
            codi = linea[:-5] #aqui tinc els 2 primers digits del cp
            ids = pool.get('res.country.cautonoma').search(cr, uid, [('code', '=', com_auto[codi])])
            if ids:
                ir.ir_set(cr, uid, 'default', 'zip='+linea[:-2], 'cautonoma', [('res.partner.address', False)], ids[0])
        con.close()
        return {}

    states = {
        'init': {
            'actions': [_crea_cpostal],
            'result': {
                'type':'form',
                'arch':cpostal_end_form,
                'fields': {},
                'state':[('end', 'Accepta', 'gtk-ok'),]
            }
        }
        
    }
l10n_ES_crea_cpostal_CA('l10n_ES_toponyms_CA.crea_cpostal')


class cautonoma(osv.osv):
    _name = 'res.country.cautonoma'
    _description = 'Comunidad Autónoma'
    _columns = {
        'country_id': fields.many2one('res.country', 'País', required=True),
        'name': fields.char('Nombre', size=64, required=True),
        'code': fields.char('Código', size=10),
            }
    _order = 'name'
cautonoma()


class res_partner_address(osv.osv):
    _name = 'res.partner.address'
    _inherit = 'res.partner.address'
    _columns = {
        'cautonoma': fields.many2one('res.country.cautonoma', 'C. Autónoma', domain="[('country_id', '=', country_id)]"),
    }
res_partner_address()
