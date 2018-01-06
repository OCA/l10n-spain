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


    def _get_selection_sii_exempt_cause(self, cr, uid, context=None):

        return self.pool.get('product.template').fields_get(cr, uid,
            allfields=['sii_exempt_cause'])['sii_exempt_cause']['selection']

    def default_sii_exempt_cause(self, cr, uid, context=None):
        default_dict = self.pool.get('product.template').\
            default_get(cr, uid, ['sii_exempt_cause'])
        return default_dict.get('sii_exempt_cause')


    _columns = {
        'sii_enabled': fields.related('company_id', 'sii_enabled',
                                      type='boolean',
                                      relation='res.company',
                                      string='SII Enabled',
                                      readonly=True),
        'sii_registration_key_sale': fields.many2one(
                'aeat.sii.mapping.registration.keys',
                'Default SII Registration Key for Sales',
                domain=[('type', '=', 'sale')]),
        'sii_registration_key_purchase': fields.many2one(
                'aeat.sii.mapping.registration.keys',
                'Default SII Registration Key for Purchases',
                domain=[('type', '=', 'purchase')]),
        'sii_active': fields.boolean('SII Active', copy=False,
                                help='Enable SII for this fiscal position?'),
        'sii_no_taxable_cause': fields.selection([
            ('ImportePorArticulos7_14_Otros',
             'No sujeta - No sujeción artículo 7, 14, otros'),
            ('ImporteTAIReglasLocalizacion',
             'Operaciones no sujetas en el TAI por reglas de localización'),
        ], 'SII No taxable cause'),
        'sii_exempt_cause': fields.selection(_get_selection_sii_exempt_cause, 'SII Exempt Cause')
    }

    _defaults = {
        'sii_no_taxable_cause': 'ImportePorArticulos7_14_Otros',
        'sii_exempt_cause': default_sii_exempt_cause,
    }


    def copy(self, cr, uid, id, default, context={}):
        default['sii_active'] = False

        return super(account_fiscal_position, self).copy(cr, uid, id, default, context=context)
