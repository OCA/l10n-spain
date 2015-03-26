# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2011
#        Pexego Sistemas Informáticos. (http://pexego.es)
#        Luis Manuel Angueira Blanco (Pexego)
#    Copyright (C) 2013
#        Ignacio Ibeas - Acysos S.L. (http://acysos.com)
#        Migración a OpenERP 7.0
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
from openerp import fields, models, api, exceptions, _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
import time
import re


class L10nEsAeatReport(models.AbstractModel):
    _name = "l10n.es.aeat.report"
    _description = "AEAT report base module"

    def _default_company(self):
        company_obj = self.env['res.company']
        return company_obj._company_default_get('l10n.es.aeat.report')

    @api.onchange('company_id')
    def on_change_company_id(self):
        """
        Loads some company data (the VAT number) when the selected
        company changes.
        """
        comp_vat = ''
        if self.company_id:
            if self.company_id.partner_id and self.company_id.partner_id.vat:
                # Remove the ES part from spanish vat numbers
                # (ES12345678Z => 12345678Z)
                comp_vat = re.match("(ES){0,1}(.*)",
                                    self.company_id.partner_id.vat).groups()[1]
        self.company_vat = comp_vat

    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=_default_company,
                                 states={'draft': [('readonly', False)]})
    company_vat = fields.Char(string='VAT number', size=9, required=True,
                              readonly=True,
                              states={'draft': [('readonly', False)]})
    phone = fields.Char(string="Phone", size=9,
                        states={'calculated': [('required', True)],
                                'confirmed': [('readonly', True)]})
    number = fields.Char(string='Declaration number', size=13,
                         required=True, readonly=True)
    previous_number = fields.Char(string='Previous declaration number',
                                  size=13,
                                  states={'done': [('readonly', True)]})
    contact_name = fields.Char(string="Full Name", size=40,
                               help="Must have name and surname.",
                               states={'calculated': [('required', True)],
                                       'confirmed': [('readonly', True)]})
    contact_phone = fields.Char(string="Phone", size=9,
                                states={'calculated': [('required', True)],
                                        'confirmed': [('readonly', True)]})
    representative_vat = fields.Char(string='L.R. VAT number', size=9,
                                     help="Legal Representative VAT number.",
                                     states={'confirmed': [('readonly',
                                                            True)]})
    fiscalyear_id = fields.Many2one('account.fiscalyear', string='Fiscal year',
                                    required=True, readonly=True,
                                    states={'draft': [('readonly', False)]})

    type = fields.Selection([('N', 'Normal'), ('C', 'Complementary'),
                             ('S', 'Substitutive')], string='Statement Type',
                            states={'calculated': [('required', True)],
                                    'done': [('readonly', True)]}, default='N')
    support_type = fields.Selection([('C', 'DVD'), ('T', 'Telematics')],
                                    string='Support Type', default='T',
                                    states={'calculated': [('required', True)],
                                            'done': [('readonly', True)]})
    calculation_date = fields.Datetime(string="Calculation date")
    state = fields.Selection([('draft', 'Draft'), ('calculated', 'Processed'),
                              ('done', 'Done'), ('cancelled', 'Cancelled')],
                             string='State', readonly=True, default='draft')

    @api.multi
    def button_calculate(self):
        res = self.calculate()
        self.write({'state': 'calculated',
                    'calculation_date': time.strftime(
                        DEFAULT_SERVER_DATETIME_FORMAT)})
        return res

    @api.multi
    def button_recalculate(self):
        self.write({'calculation_date':
                    time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
        return self.calculate()

    @api.multi
    def calculate(self):
        return True

    @api.multi
    def button_confirm(self):
        """Set report status to done."""
        self.write({'state': 'done'})
        return True

    @api.multi
    def button_cancel(self):
        """Set report status to cancelled."""
        self.write({'state': 'cancelled'})
        return True

    @api.multi
    def button_recover(self):
        """Set report status to draft and reset calculation date."""
        self.write({'state': 'draft', 'calculation_date': None})
        return True

    @api.multi
    def button_export(self):
        for report in self:
            export_obj = self.env["l10n.es.aeat.report.%s.export_to_boe" %
                                  report.number]
            export_obj.export_boe_file(report)
        return True

    @api.multi
    def unlink(self):
        for item in self:
            if item.state not in ['draft', 'cancelled']:
                raise exceptions.Warning(_("Only reports in 'draft' or "
                                           "'cancelled' state can be removed"))
        return super(L10nEsAeatReport, self).unlink()

    def __init__(self, pool, cr):
        super(L10nEsAeatReport, self).__init__(pool, cr)
        try:
            getattr(self, '_aeat_number')
        except:
            pass
            # raise exceptions.Warning(
            #    "Modelo no válido. Debe declarar una variable '_aeat_number'")
