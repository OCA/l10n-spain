# coding: utf-8
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2017 Domatix Technologies  S.L. (http://www.domatix.com)
#                       info <info@domatix.com>
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

from odoo import models, fields, api, _

EXPIRED_WARNING_AEAT = {
    'title': _('Warning!'),
    'message': _('The AEAT certificate for this supplier '
                 'has expired')
    }

REQUIRED_WARNING_AEAT = {
    'title': _('Warning!'),
    'message': _('The AEAT certificate is required and '
                 'expiration date is not set')
    }

EXPIRED_WARNING_SS = {
    'title': _('Warning!'),
    'message': _('The SS certificate for this supplier '
                 'has expired')
    }

REQUIRED_WARNING_SS = {
    'title': _('Warning!'),
    'message': _('The SS certificate is required and '
                 'expiration date is not set')
    }


class PurchaseOrder(models.Model):
    _inherit = ['purchase.order']

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super(PurchaseOrder, self).onchange_partner_id()
        if not self.partner_id:
            return res
        if self.partner_id.certificate_required:
            if not self.partner_id.certificate_expiration_aeat:
                res['warning'] = REQUIRED_WARNING_AEAT
            elif self.partner_id.certificate_expired_aeat:
                res['warning'] = EXPIRED_WARNING_AEAT
            elif not self.partner_id.certificate_expiration_ss:
                res['warning'] = REQUIRED_WARNING_SS
            elif self.partner_id.certificate_expired_ss:
                res['warning'] = EXPIRED_WARNING_SS
        return res
