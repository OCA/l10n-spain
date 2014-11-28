# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 Ting (http://www.ting.es)
#    Copyright (c) 2011-2013 Acysos S.L.(http://acysos.com)
#                       Ignacio Ibeas Izquierdo <ignacio@acysos.com>
#    Copyright (c) 2011 NaN Projectes de Programari Lliure, S.L.
#                       http://www.NaN-tic.com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

from openerp.osv import orm, fields
import time
from openerp import netsvc


class L10nEsAeatMod340Report(orm.Model):

    def button_calculate(self, cr, uid, ids, args, context=None):
        calculate_obj = self.pool['l10n.es.aeat.mod340.calculate_records']
        calculate_obj._wkf_calculate_records(cr, uid, ids, context)
        return True

    def button_recalculate(self, cr, uid, ids, context=None):
        calculate_obj = self.pool['l10n.es.aeat.mod340.calculate_records']
        calculate_obj._calculate_records(cr, uid, ids, context)
        return True

    def _name_get(self, cr, uid, ids, field_name, arg, context=None):
        """Returns the report name"""
        result = {}
        for report in self.browse(cr, uid, ids, context=context):
            result[report.id] = report.number
        return result

    def _get_number_records(self, cr, uid, ids, field_name, args,
                            context=None):
        result = {}
        for id in ids:
            result[id] = {}.fromkeys(
                   ['number_records', 'total_taxable', 'total_sharetax',
                    'total', 'total_taxable_rec', 'total_sharetax_rec',
                    'total_rec'], 0.0
                 )
        for model in self.browse(cr, uid, ids, context=context):
            for issue in model.issued:
                result[model.id]['number_records'] += len(issue.tax_line_ids)
                result[model.id]['total_taxable'] += issue.base_tax
                result[model.id]['total_sharetax'] += issue.amount_tax
                result[model.id]['total'] += issue.base_tax + issue.amount_tax
            for issue in model.received:
                result[model.id]['number_records'] += len(issue.tax_line_ids)
                result[model.id]['total_taxable_rec'] += issue.base_tax
                result[model.id]['total_sharetax_rec'] += issue.amount_tax
                result[model.id]['total_rec'] += issue.base_tax
                result[model.id]['total_rec'] += issue.amount_tax
        return result

    _inherit = "l10n.es.aeat.report"
    _name = 'l10n.es.aeat.mod340.report'
    _description = 'Model 340'
    _columns = {
        'name': fields.function(_name_get, method=True, type="char",
                                size=64, string="Name"),
        'declaration_number': fields.char("Declaration number", size=64,
                                          readonly=True),
        'phone_contact': fields.char('Phone Contact', size=9),
        'name_contact': fields.char('Name And Surname Contact', size=40),
        'period_from': fields.many2one('account.period', 'Start period',
                                       states={'done': [('readonly', True)]}),
        'period_to': fields.many2one('account.period', 'End period',
                                     states={'done': [('readonly', True)]}),
        'issued': fields.one2many('l10n.es.aeat.mod340.issued', 'mod340_id',
                                  'Invoices Issued',
                                  states={'done': [('readonly', True)]}),
        'received': fields.one2many('l10n.es.aeat.mod340.received',
                                    'mod340_id', 'Invoices Received',
                                    states={'done': [('readonly', True)]}),
        'investment': fields.one2many('l10n.es.aeat.mod340.investment',
                                      'mod340_id', 'Property Investment'),
        'intracomunitarias': fields.one2many(
            'l10n.es.aeat.mod340.intracomunitarias',
            'mod340_id', 'Operations Intracomunitarias'),
        'ean13': fields.char('Electronic Code VAT reverse charge', size=16),
        'total_taxable':  fields.function(
            _get_number_records, method=True, type='float',
            string='Total Taxable', multi='recalc',
            help="The declaration will include partners with the total "
            "of operations over this limit"),
        'total_sharetax': fields.function(
            _get_number_records, method=True,
            type='float', string='Total Share Tax', multi='recalc',
            help="The declaration will include partners with the total "
            "of operations over this limit"),
        'number_records': fields.function(
            _get_number_records, method=True, type='integer', string='Records',
            multi='recalc',
            help="The declaration will include partners with the total "
            "of operations over this limit"),
        'total': fields.function(
            _get_number_records, method=True, type='float', string="Total",
            multi='recalc',
            help="The declaration will include partners with the total "
            "of operations over this limit"),
        'total_taxable_rec':  fields.function(
            _get_number_records, method=True,
            type='float', string='Total Taxable', multi='recalc',
            help="""The declaration will include partners with the total 
                of operations over this limit"""),
        'total_sharetax_rec': fields.function(
            _get_number_records, method=True,
            type='float', string='Total Share Tax', multi='recalc',
            help="""The declaration will include partners with the total 
                of operations over this limit"""),
        'total_rec': fields.function(
            _get_number_records, method=True,
            type='float', string="Total", multi='recalc',
            help="""The declaration will include partners with the total 
                of operations over this limit"""),
        'calculation_date': fields.date('Calculation date', readonly=True),
    }

    _defaults = {
        'number': '340',
        'declaration_number': '340',
    }

    def set_done(self, cr, uid, id, *args):
        self.write(cr, uid, id, {'calculation_date': time.strftime('%Y-%m-%d'),
                                 'state': 'done'})
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'l10n.es.aeat.mod340.report', id, 'done',
                                cr)
        return True

    def action_confirm(self, cr, uid, ids, context=None):
        """set to done the report and check its records"""
        self.check_report(cr, uid, ids, context)
        self.write(cr, uid, ids, {'state': 'done'})
        return True


class L10nEsAeatMod340Issued(orm.Model):
    _name = 'l10n.es.aeat.mod340.issued'
    _description = 'Invoices invoice'
    _columns = {
        'mod340_id': fields.many2one('l10n.es.aeat.mod340.report', 'Model 340',
                                     ondelete="cascade"),
        'partner_id': fields.many2one('res.partner', 'Partner',
                                      ondelete="cascade"),
        'partner_vat': fields.char('Company CIF/NIF', size=12),
        'representative_vat': fields.char(
            'L.R. VAT number', size=9, help="Legal Representative VAT number"),
        'partner_country_code': fields.char('Country Code', size=2),
        'invoice_id': fields.many2one('account.invoice', 'Invoice',
                                      ondelete="cascade"),
        'base_tax': fields.float('Base tax bill', digits=(13, 2)),
        'amount_tax': fields.float('Total tax', digits=(13, 2)),
        'total': fields.float('Total', digits=(13, 2)),
        'tax_line_ids': fields.one2many('l10n.es.aeat.mod340.tax_line_issued',
                                        'invoice_record_id', 'Tax lines'),
        'date_invoice': fields.date('Date Invoice', readonly=True),
    }

    _order = 'date_invoice asc, invoice_id asc'


class L10nEsAeatMod340Received(orm.Model):
    _name = 'l10n.es.aeat.mod340.received'
    _description = 'Invoices Received'
    _inherit = 'l10n.es.aeat.mod340.issued'
    _columns = {
        'tax_line_ids': fields.one2many(
            'l10n.es.aeat.mod340.tax_line_received', 'invoice_record_id',
            'Tax lines'),
    }


class L10nEsAeatMod340Investment(orm.Model):
    _name = 'l10n.es.aeat.mod340.investment'
    _description = 'Property Investment'
    _inherit = 'l10n.es.aeat.mod340.issued'


class L10nEsAeatMod340Intracomunitarias(orm.Model):
    _name = 'l10n.es.aeat.mod340.intracomunitarias'
    _description = 'Operations Intracomunitarias'
    _inherit = 'l10n.es.aeat.mod340.issued'


class L10nEsAeatMod340TaxLineIssued(orm.Model):
    _name = 'l10n.es.aeat.mod340.tax_line_issued'
    _description = 'Mod340 vat lines issued'
    _columns = {
        'name': fields.char('Name', size=128, required=True, select=True),
        'tax_percentage': fields.float('Tax percentage', digits=(0, 2)),
        'tax_amount': fields.float('Tax amount', digits=(13, 2)),
        'base_amount': fields.float('Base tax bill', digits=(13, 2)),
        'invoice_record_id': fields.many2one(
            'l10n.es.aeat.mod340.issued', 'Invoice issued', required=True,
            ondelete="cascade", select=1),
    }


class L10nEsAeatMod340TaxLineReceived(orm.Model):
    _name = 'l10n.es.aeat.mod340.tax_line_received'
    _description = 'Mod340 vat lines received'
    _inherit = 'l10n.es.aeat.mod340.tax_line_issued'
    _columns = {
        'invoice_record_id': fields.many2one(
            'l10n.es.aeat.mod340.received', 'Invoice received', required=True,
            ondelete="cascade", select=1),
    }
