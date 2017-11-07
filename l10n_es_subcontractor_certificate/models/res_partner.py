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
