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


class ResPartner(models.Model):
    _inherit = ['res.partner']

    certificate_required = fields.Boolean(string='Certificate Required')
    certificate_expiration_aeat = fields.Date(
        string='AEAT Certificate Expiration')
    certificate_expired_aeat = fields.Boolean(
        string='AEAT Certificate Expirated',
        compute='_compute_certificate_expired_aeat')
    certificate_expiration_ss = fields.Date(string='SS Certificate Expiration')
    certificate_expired_ss = fields.Boolean(
        string='SS Certificate Expirated',
        compute='_compute_certificate_expired_ss')

    def _compute_certificate_expired_aeat(self):
        self.certificate_expired_aeat = self.certificate_expiration_aeat and \
            (self.certificate_expiration_aeat < fields.Date.today())

    def _compute_certificate_expired_ss(self):
        self.certificate_expired_ss = self.certificate_expiration_ss and \
            (self.certificate_expiration_ss < fields.Date.today())


class PurchaseOrder(models.Model):
    _inherit = ['purchase.order']

    @api.multi
    def onchange_partner_id(self, partner_id):
        res = super(PurchaseOrder, self).onchange_partner_id(partner_id)
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)[0]
            if partner.certificate_required:
                if not partner.certificate_expiration_aeat:
                    res['warning'] = REQUIRED_WARNING_AEAT
                elif partner.certificate_expired_aeat:
                    res['warning'] = EXPIRED_WARNING_AEAT
                elif not partner.certificate_expiration_ss:
                    res['warning'] = REQUIRED_WARNING_SS
                elif partner.certificate_expired_ss:
                    res['warning'] = EXPIRED_WARNING_SS
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
            if partner.certificate_required:
                if not partner.certificate_expiration_aeat:
                    res['warning'] = REQUIRED_WARNING_AEAT
                elif partner.certificate_expired_aeat:
                    res['warning'] = EXPIRED_WARNING_AEAT
                elif not partner.certificate_expiration_ss:
                    res['warning'] = REQUIRED_WARNING_SS
                elif partner.certificate_expired_ss:
                    res['warning'] = EXPIRED_WARNING_SS
        return res
