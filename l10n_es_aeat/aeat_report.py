# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2011
#        Pexego Sistemas Informáticos. (http://pexego.es) All Rights Reserved
#        Luis Manuel Angueira Blanco (Pexego)
#    Copyright (C) 2013
#        Ignacio Ibeas - Acysos S.L. (http://acysos.com) All Rights Reserved
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
from openerp.tools.translate import _
from openerp.osv import orm, fields
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
import time
import re


class L10nEsAeatReport(orm.Model):
    _name = "l10n.es.aeat.report"
    _description = "AEAT report base module"

    def on_change_company_id(self, cr, uid, ids, company_id):
        """
        Loads some company data (the VAT number) when the selected
        company changes.
        """
        company_vat = ''
        if company_id:
            company = self.pool['res.company'].browse(cr, uid, company_id)
            if company.partner_id and company.partner_id.vat:
                # Remove the ES part from spanish vat numbers
                # (ES12345678Z => 12345678Z)
                company_vat = re.match("(ES){0,1}(.*)",
                                       company.partner_id.vat).groups()[1]
        return {'value': {'company_vat': company_vat}}

    _columns = {
        'company_id': fields.many2one('res.company', 'Company', required=True,
                                      readonly=True,
                                      states={'draft': [('readonly', False)]}),
        'number': fields.char('Declaration number', size=13, required=True,
                              readonly=True),
        'previous_number': fields.char('Previous declaration number',
                                       size=13,
                                       states={'done': [('readonly', True)]}),
        'representative_vat': fields.char('L.R. VAT number', size=9,
                                          help="Legal Representative VAT number.",
                                          states={'confirmed': [('readonly', True)]}),
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal year',
                                         required=True, readonly=True,
                                         states={'draft': [('readonly', False)]}),
        'company_vat': fields.char('VAT number', size=9, required=True,
                                   readonly=True, states={'draft': [('readonly', False)]}),
        'type': fields.selection([('N', 'Normal'),
                                  ('C', 'Complementary'),
                                  ('S', 'Substitutive')],
                                 'Statement Type',
                                 states={'calculated': [('required', True)],
                                         'done': [('readonly', True)]}),
        'support_type': fields.selection([('C', 'DVD'),
                                          ('T', 'Telematics')],
                                         'Support Type',
                                         states={'calculated': [('required', True)],
                                                 'done': [('readonly', True)]}),
        'calculation_date': fields.datetime("Calculation date"),
        'state': fields.selection([('draft', 'Draft'),
                                   ('calculated', 'Processed'),
                                   ('done', 'Done'),
                                   ('cancelled', 'Cancelled')],
                                  'State', readonly=True),
    }

    _defaults = {
        'company_id': lambda self, cr, uid, context=None: (
            self.pool['res.company']._company_default_get(cr, uid, 'l10n.es.aeat.report', context=context)),
        'type': 'N',
        'support_type': 'T',
        'state': 'draft',
    }

    def button_calculate(self, cr, uid, ids, context=None):
        res = self.calculate(cr, uid, ids, context=context)
        self.write(cr, uid, ids,
                   {'state': 'calculated',
                    'calculation_date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
        return res

    def button_recalculate(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids,
                   {'calculation_date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
        return self.calculate(cr, uid, ids, context=context)

    def calculate(self, cr, uid, ids, context=None):
        return True

    def button_confirm(self, cr, uid, ids, context=None):
        """Set report status to done."""
        self.write(cr, uid, ids, {'state': 'done'}, context=context)
        return True

    def button_cancel(self, cr, uid, ids, context=None):
        """Set report status to cancelled."""
        self.write(cr, uid, ids, {'state': 'cancelled'}, context=context)
        return True

    def button_recover(self, cr, uid, ids, context=None):
        """Set report status to draft and reset calculation date."""
        self.write(cr, uid, ids, {'state': 'draft', 'calculation_date': None})
        return True

    def button_export(self, cr, uid, ids, context=None):
        for report in self.browse(cr, uid, ids, context=context):
            export_obj = self.pool["l10n.es.aeat.report.%s.export_to_boe" % report.number]
            export_obj.export_boe_file(cr, uid, report, context=context)
        return True

    def unlink(self, cr, uid, ids, context=None):
        for item in self.browse(cr, uid, ids):
            if item.state not in ['draft', 'cancelled']:
                raise orm.except_orm(_('Error!'),
                                     _("Only reports in 'draft' or "
                                       "'cancelled' state can be removed"))
        return super(L10nEsAeatReport, self).unlink(cr, uid, ids, context=context)
