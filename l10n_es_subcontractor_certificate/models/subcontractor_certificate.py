# Copyright 2014 Domatix Technologies S.L. - Angel Moya
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

from odoo import _, api, fields, models

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
        for partner in self:
            partner.certificate_expired_aeat = (
                partner.certificate_expiration_aeat and
                (partner.certificate_expiration_aeat < fields.Date.today()))

    def _compute_certificate_expired_ss(self):
        for partner in self:
            partner.certificate_expired_ss = (
                partner.certificate_expiration_ss and
                (partner.certificate_expiration_ss < fields.Date.today()))


class PurchaseOrder(models.Model):
    _inherit = ['purchase.order']

    @api.onchange('partner_id', 'company_id')
    def onchange_partner_id(self):
        res = super(PurchaseOrder, self).onchange_partner_id() or {}
        partner = self.partner_id
        if partner:
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

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        res = super(AccountInvoice, self)._onchange_partner_id() or {}
        if self.type == 'in_invoice' and self.partner_id:
            partner = self.partner_id
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
