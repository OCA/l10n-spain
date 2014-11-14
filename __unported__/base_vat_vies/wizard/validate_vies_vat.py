# -*- coding: utf-8 -*-
#########################################################################
#                                                                       #
# Copyright (C) 2012 Factor Libre SL                                    #
#                                                                       #
#This program is free software: you can redistribute it and/or modify   #
#it under the terms of the GNU General Public License as published by   #
#the Free Software Foundation, either version 3 of the License, or      #
#(at your option) any later version.                                    #
#                                                                       #
#This program is distributed in the hope that it will be useful,        #
#but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#GNU General Public License for more details.                           #
#                                                                       #
#You should have received a copy of the GNU General Public License      #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#########################################################################

from osv import osv
from openerp.tools.translate import _

import vatnumber


class validate_vies_vat(osv.osv_memory):
    _name = 'validate.vies.vat'

    def _split_vat(self, vat):
        vat_country, vat_number = vat[:2].lower(), vat[2:].replace(' ', '')
        return vat_country, vat_number

    def check_customer_vat(self, cr, uid, vat_country, vat_number):
        partner_obj = self.pool.get('res.partner')
        if not hasattr(partner_obj, 'check_vat_' + vat_country):
            return False
        check = getattr(partner_obj, 'check_vat_' + vat_country)
        if not check(vat_number):
            return False
        return True

    def validate_vies(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        values = {}
        partner_obj = self.pool.get('res.partner')
        for partner in partner_obj.browse(cr, uid, context.get('active_ids'), context=context):
            values['valid_vies_vat'] = False
            if partner.vat:
                vat = self._split_vat(partner.vat)
                if self.check_customer_vat(cr, uid, vat[0], vat[1]):
                    if vatnumber.check_vies(partner.vat):
                        values['valid_vies_vat'] = True
                else:
                    raise osv.except_osv(
                        _("Error"), _("Client Vat Number not have a valid format"))
                    return {'type': 'ir.actions.act_window_close'}
            partner_obj.write(cr, uid, [partner.id], values)
        return {'type': 'ir.actions.act_window_close'}

validate_vies_vat()
