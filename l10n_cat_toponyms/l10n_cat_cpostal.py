# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
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

import ir
import wizard
import pooler
from osv import osv, fields
import codecs
import tools

cpostal_end_form = '''<?xml version="1.0" encoding="utf-8"?>
<form string="Codis postals">
    <separator string="Resultat:" colspan="4"/>
    <label string="S'han associat les comarques dels Països Catalans (Catalunya, País Valencià i Illes Balears) als codis postals." colspan="4" align="0.0"/>
    <label string="Permet omplenar automàticament el camp comarca del formulari d'empresa i contacte a partir del codi postal." colspan="4" align="0.0"/>
</form>'''

class l10n_cat_crea_cpostal(wizard.interface):
    def _crea_cpostal(self, cr, uid, data, context):
        from comarca_cpostal import cod_postales
        pool = pooler.get_pool(cr.dbname)
        for m in cod_postales:
            ids = pool.get('res.country.state.comarca').search(cr, uid, [('name', '=', m[1])])
            if ids:
                ir.ir_set(cr, uid, 'default', 'zip='+m[0], 'comarca', [('res.partner.address', False)], ids[0])
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
l10n_cat_crea_cpostal('l10n_cat_toponyms.crea_cpostal')


class comarca(osv.osv):
    _name = 'res.country.state.comarca'
    _description = 'Comarca'
    _columns = {
        'state_id': fields.many2one('res.country.state', 'Regió', required=True, select=1),
        'name': fields.char('Comarca', size=64, required=True),
        'code': fields.char('Codi comarca', size=10),
    }
    _order = 'name'
comarca()


class res_partner_address(osv.osv):
    _name = 'res.partner.address'
    _inherit = 'res.partner.address'
    _columns = {
        'comarca': fields.many2one('res.country.state.comarca', 'Comarca', domain="[('state_id', '=', state_id)]"),
    }
res_partner_address()
