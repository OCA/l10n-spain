# -*- coding: utf-8 -*-
# (c) 2017 Diagram Software S.L.
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.osv import osv, fields
from openerp.tools.translate import _


class L10nEsAeatSii(osv.Model):
    _name = 'l10n.es.aeat.sii'

    _columns = {
        'name': fields.char(string="Name", size=64),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('active', 'Active')
        ], string="State", default="draft"),
        'file': fields.binary(string="File", required=True),
        'path_folder': fields.char(string="Path Name", required=True, size=64),
        'folder': fields.char(string="Folder", required=True, size=64),

        'date_start': fields.date(string="Start Date"),
        'date_end': fields.date(string="End Date"),
        'public_key': fields.char(string="Public Key", readonly=True, size=64),
        'private_key': fields.char(string="Private Key", readonly=True, size=64),
        'company_id': fields.many2one("res.company", string="Compañia", required=True
                                      )

    }

    _defaults = {
        'state': 'draft'

    }

    def load_password_wizard(self, cr, uid, ids, context={}):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Insert Password'),
            'res_model': 'l10n.es.aeat.sii.password',
            'view_mode': 'form',
            'view_type': 'form',
            'views': [(False, 'form')],
            'target': 'new',
        }

    def action_activate(self, cr, uid, ids, context={}):

        for aeat_sii in self.browse(cr, uid, ids, context=context):

            other_configs = self.search(cr, uid, [('id', '!=', aeat_sii.id),('company_id', '=', aeat_sii.company_id.id)])
            for config_id in self.browse(cr, uid, other_configs):
                self.write(cr, uid, config_id.id, {'state': 'draft'})
            self.write(cr, uid, aeat_sii.id, {'state': 'active'})
        return {'type': 'ir.actions.act_window_close'}
