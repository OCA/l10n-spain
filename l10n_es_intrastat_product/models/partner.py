# -*- encoding: utf-8 -*-
##############################################################################
#
#    Report intrastat product module for Odoo
#    Copyright (C) 2011-2014 Akretion (http://www.akretion.com)
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    intrastat_fiscal_representative = fields.Many2one(
        'res.partner', string="EU fiscal representative",
        help="If this partner is located outside the EU but you "
        "deliver the goods inside the UE, the partner needs to "
        "have a fiscal representative with a VAT number inside the EU. "
        "In this scenario, the VAT number of the fiscal representative "
        "will be used for the Intrastat Product report (DEB).")

    # Copy field 'intrastat_fiscal_representative' from company partners
    # to their contacts
    @api.model
    def _commercial_fields(self):
        res = super(ResPartner, self)._commercial_fields()
        res.append('intrastat_fiscal_representative')
        return res

    @api.one
    @api.constrains('intrastat_fiscal_representative')
    def _check_fiscal_representative(self):
        '''The Fiscal rep. must be based in the same country as our '''
        '''company or in an intrastat country'''
        if self.intrastat_fiscal_representative:
            if not self.intrastat_fiscal_representative.country_id:
                raise ValidationError(
                    _("The fiscal representative '%s' of partner '%s' "
                        "must have a country.")
                    % (self.intrastat_fiscal_representative.name, self.name))
            if (not self.intrastat_fiscal_representative.country_id.intrastat
                    and self.intrastat_fiscal_representative.country_id
                    != self.env.user.company_id.partner_id.country_id):
                raise ValidationError(
                    _("The fiscal representative '%s' of partner '%s' "
                        "must be based in an EU country.")
                    % (self.intrastat_fiscal_representative.name, self.name))
            if not self.intrastat_fiscal_representative.vat:
                raise ValidationError(
                    _("The fiscal representative '%s' of partner '%s' "
                        "must have a VAT number.")
                    % (self.intrastat_fiscal_representative.name, self.name))
