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



from openerp.osv import fields, osv


class account_fiscal_position(osv.Model):
    _inherit = 'account.fiscal.position'

    _columns = {
        'sii_registration_key_sale': fields.many2one(
                'aeat.sii.mapping.registration.keys',
                'Default SII Registration Key for Sales',
                domain=[('type', '=', 'sale')]),
        'sii_registration_key_purchase': fields.many2one(
                'aeat.sii.mapping.registration.keys',
                'Default SII Registration Key for Purchases',
                domain=[('type', '=', 'purchase')]),
        'sii_active': fields.boolean('SII Active', copy=False,
                                help='Enable SII for this fiscal position?')
    }


    def copy(self, cr, uid, id, default, context={}):
        default['sii_active'] = False

        return super(account_fiscal_position, self).copy(cr, uid, id, default, context=context)
