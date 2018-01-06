# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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
from tools.translate import _


class l10n_es_aeat_sii(osv.osv):
    _name = 'l10n.es.aeat.sii'

    _columns = {
        'name': fields.char('Name', size=64),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('active', 'Active')
        ], 'State'),
        'file': fields.binary('File', required=True),
        'folder': fields.char('Folder', required=True, size=64),
        'date_start': fields.date('Start Date'),
        'date_end': fields.date('End Date'),
        'public_key': fields.char('Public Key', readonly=True, size=64),
        'private_key': fields.char('Private Key', readonly=True, size=64),
        'company_id': fields.many2one('res.company', 'Company', required=True),
    }

    _defaults = {
        'state': 'draft',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
    }

    def load_password_wizard(self, cr, uid, ids, context=None):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Insert Password'),
            'res_model': 'l10n.es.aeat.sii.password',
            'view_mode': 'form',
            'view_type': 'form',
            'views': [(False, 'form')],
            'target': 'new',
        }

    def action_active(self, cr, uid, ids, context=None):
        for aeat_sii in self.browse(cr, uid, ids, context=context):
            self.write(cr, uid, aeat_sii.id, {'state': 'active'})

        return {'type': 'ir.actions.act_window_close'}

l10n_es_aeat_sii()
