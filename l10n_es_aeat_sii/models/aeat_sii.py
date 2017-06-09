# -*- coding: utf-8 -*-
# (c) 2017 Diagram Software S.L.
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from osv import osv, fields
from tools.translate import _


class L10nEsAeatSii(osv.osv):
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

    def action_active(self, cr, uid, ids, context={}):
        conf = self.pool.get("ir.config_parameter")
        for aeat_sii in self.browse(cr, uid, ids, context=context):

            # TODO use ref

            if aeat_sii.public_key:
                sii_crt = conf.search(cr, uid, [('key', '=', 'l10n_es_aeat_sii.publicCrt')])
                if sii_crt:
                    conf.write(cr, uid, sii_crt, {'value': aeat_sii.public_key})
            if aeat_sii.private_key:
                sii_key = conf.search(cr, uid, [('key', '=', 'l10n_es_aeat_sii.privateKey')])
                if sii_key:
                    conf.write(cr, uid, sii_key, {'value': aeat_sii.private_key})

            other_configs = self.search(cr, uid, [('id', '!=', aeat_sii.id)])
            for config_id in self.browse(cr, uid, other_configs):
                self.write(cr, uid, config_id.id, {'state': 'draft'})
            self.write(cr, uid, aeat_sii.id, {'state': 'active'})
        return {'type': 'ir.actions.act_window_close'}

L10nEsAeatSii()

