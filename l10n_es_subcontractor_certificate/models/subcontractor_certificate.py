# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2014 Domatix Technologies  S.L. (http://www.domatix.com)
#                       info <info@domatix.com>
#                        Angel Moya <angel.moya@domatix.com>
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

from openerp import models, fields, api, _

EXPIRED_WARNING = {
    'title': _('Warning!'),
    'message': _('The subcontractor certificate for this supplier \
                    has expired, or is not set.')
    }


class ResPartner(models.Model):
    _inherit = ['res.partner']

    certificate_required = fields.Boolean(string='Certificate Required')
    certificate_expiration = fields.Date(string='Certificate Expiration')

    @api.one
    def certificate_expired(self):
        return self.certificate_required and (
            not self.certificate_expiration
            or (self.certificate_expiration
                < fields.date.today().strftime("%Y-%m-%d")
                )
            )


class PurchaseOrder(models.Model):
    _inherit = ['purchase.order']

    @api.multi
    def onchange_partner_id(self, partner_id):
        res = super(PurchaseOrder, self).onchange_partner_id(partner_id)
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)[0]
            if partner.certificate_expired()[0]:
                res['warning'] = EXPIRED_WARNING
        return res


class AccountInvoice(models.Model):
    _inherit = ['account.invoice']

    @api.multi
    def onchange_partner_id(self, type, partner_id, date_invoice=False,
                            payment_term=False, partner_bank_id=False,
                            company_id=False):
        res = super(AccountInvoice, self).onchange_partner_id(
            type, partner_id, date_invoice=False,
            payment_term=False, partner_bank_id=False,
            company_id=False)
        if type == 'in_invoice' and partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            if partner.certificate_expired()[0]:
                res['warning'] = EXPIRED_WARNING
        return res
