# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Model 347 Aeat
#    Copyright (c) 2009 Alejandro Sanchez (http://www.asr-oss.com) All Rights Reserved.
#                       Alejandro Sanchez <alejandro@asr-oss.com>
#    $Id$
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
"""
AEAT 347 model object and detail lines.
"""

from osv import osv, fields
import netsvc
import re
from tools.translate import _

class l10n_es_aeat_mod347_report(osv.osv):
    """
    Represents an AEAT 347 report for a given company and fiscal year.
    """

    _name = 'l10n.es.aeat.mod347.report'
    _description = 'AEAT 347 Report'

    def _get_totals(self, cr, uid, ids, name, args, context=None):
        """
        Calculates the total_* fields from the line values.
        """
        if context is None:
            context = {}
        res = {}
        for report in self.browse(cr, uid, ids, context=context):
            res[report.id] = {
                'total_partner_records': 0,
                'total_amount': 0.0,
                'total_cash_amount': 0.0,
                'total_real_state_transmissions_amount': 0.0,
                'total_real_state_records': 0,
                'total_real_state_amount': 0,
            }
            for partner_record in report.partner_record_ids:
                res[report.id]['total_partner_records'] += 1
                res[report.id]['total_amount'] += partner_record.amount
                res[report.id]['total_cash_amount'] += partner_record.cash_amount
                res[report.id]['total_real_state_transmissions_amount'] += partner_record.real_state_transmissions_amount
            for real_state_record in report.real_state_record_ids:
                res[report.id]['total_real_state_records'] += 1
                res[report.id]['total_real_state_amount'] += real_state_record.amount

        return res

    def _name_get(self, cr, uid, ids, field_name, arg, context={}):
        """
        Returns the report name
        """
        result = {}
        for report in self.browse(cr, uid, ids, context):
            result[report.id] = str(report.number)
        return result

    def _get_period_names(self, cr, uid, ids, field_name, arg, context={}):
        """
        Returns the period names to put in generic_report.rml
        """
        result = {}
        for report in self.browse(cr, uid, ids, context):            
                result[report.id] = ', '.join([ period.name for period in report.period_ids])
        return result

    _columns = {
        # The name it's just an alias of the number
        'name': fields.function(_name_get, method=True, type="char", size="64", string="Name"),

        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fical Year', required=True),
        'period_ids': fields.many2many('account.period', 'mod347_report_periods', 'mod347_id', 'period_id', 'Periods'),
        'period_names': fields.function(_get_period_names, string="Periods", method=True, type='char', size=128),
        
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'number': fields.integer('Declaration Number', size=13),
        'support_type': fields.selection([('C','DVD'),('T','Telematics')], 'Support Type'),

        'company_vat': fields.char('VAT number', size=9),
        'representative_vat': fields.char('L.R. VAT number', size=9, help="Legal Representative VAT number"),
        'contact_name': fields.char("Full Name", size=40),
        'contact_phone': fields.char("Phone", size=9),

        'type': fields.selection([(' ','Normal'),('C','Complementary'),('S','Substitutive')], 'Statement Type'),
	'previous_number': fields.integer('Previous Declaration Number', size=13),

        #
        # Limits
        #
        'operations_limit': fields.float('Invoiced Limit (1)', digits=(13,2), help="The declaration will include partners with the total of operations over this limit"),
        'received_cash_limit': fields.float('Received cash Limit (2)', digits=(13,2), help="The declaration will show the total of cash operations over this limit"),
        'charges_obtp_limit': fields.float('Charges on behalf of third parties Limit (3)', digits=(13,2), help="The declaration will include partners from which we received payments, on behalf of third parties, over this limit"),

        #
        # Totals
        #
        'total_partner_records': fields.function(_get_totals, string="Partners records", method=True, type='integer', multi="totals_multi"),
        'total_amount': fields.function(_get_totals, string="Amount", method=True, type='float', multi="totals_multi"),
        'total_cash_amount': fields.function(_get_totals, string="Cash Amount", method=True, type='float', multi="totals_multi"),
        'total_real_state_transmissions_amount': fields.function(_get_totals, string="Real State Transmissions Amount", method=True, type='float', multi="totals_multi"),
        'total_real_state_records': fields.function(_get_totals, string="Real state records", method=True, type='integer', multi="totals_multi"),
        'total_real_state_amount': fields.function(_get_totals, string="Real State Amount", method=True, type='float', multi="totals_multi"),

        # Date of the last calculation
        'calc_date': fields.datetime("Calculation date"),
        # State of the report
        'state': fields.selection([('draft','Draft'),('calc','Processing'),('calc_done','Processed'),('done','Done'),('canceled','Canceled')], 'State'),
    }
    _defaults = {
        # Current company by default:
        'company_id': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid, context).company_id.id,
        # Draft state by default:
        'state': lambda *a: 'draft',

        #
        # Default limits
        #
        'operations_limit': lambda *args: 3005.06,
        'charges_obtp_limit': lambda *args: 300.51,
        'received_cash_limit': lambda *args: 6000.00,

        #
        # Default types
        #
        'type': lambda *args: ' ',
        'support_type': lambda *args: 'T',
    }

    def on_change_company_id(self, cr, uid, ids, company_id):
        """
        Loads some company data (the VAT number) when the selected
        company changes.
        """
        company_vat = ''
        if company_id:
            company = self.pool.get('res.company').browse(cr, uid, company_id)
            if company.partner_id and company.partner_id.vat:
                # Remove the ES part from spanish vat numbers (ES12345678Z => 12345678Z)
                company_vat = re.match("(ES){0,1}(.*)", company.partner_id.vat).groups()[1]
        return  { 'value': { 'company_vat': company_vat } }



    def action_calculate(self, cr, uid, ids, context=None):
        """
        Called when the report is calculated.
        """
        # Note: Just change the state, everything else is done on the calculate wizard.
        self.write(cr, uid, ids, {'state': 'calc_done'})
        return True

    def _check_report_lines(self, cr, uid, ids, context=None):
        """checks report lines"""
        if context is None: context = {}

        for item in self.browse(cr, uid, ids, context):
            ## Browse partner record lines to check if all are correct (all fields filled)
            for partner_record in item.partner_record_ids:
                if not partner_record.partner_state_code:
                    raise osv.except_osv(_('Error!'), _("All partner state code field must be filled."))
                if not partner_record.partner_vat:
                    raise osv.except_osv(_('Error!'), _("All partner vat number field must be filled."))

            for real_state_record in item.real_state_record_ids:
                if not real_state_record.state_code:
                    raise osv.except_osv(_('Error!'), _("All real state records state code field must be filled."))

        return True


    def check_report(self, cr, uid, ids, context=None):
        """Different check out in report"""
        if context is None: context = {}

        self._check_report_lines(cr, uid, ids, context)

        return True

    def action_confirm(self, cr, uid, ids, context=None):
        """
        Called when the user clicks the confirm button.
        """
        if context is None: context = {}

        self.check_report(cr, uid, ids, context)
        self.write(cr, uid, ids, {'state': 'done'})
        return True

    def action_cancel(self, cr, uid, ids, context=None):
        """
        Called when the user clicks the cancel button.
        """
        self.write(cr, uid, ids, {'state': 'canceled'})
        return True

    def action_recover(self, cr, uid, ids, context=None):
        """
        Called when the user clicks the draft button to create
        a new workflow instance.
        """
        self.write(cr, uid, ids, {'state': 'draft', 'calc_date': None})
        wf_service = netsvc.LocalService("workflow")
        for item_id in ids:
            wf_service.trg_create(uid, 'l10n.es.aeat.mod347.report', item_id, cr)
        return True


l10n_es_aeat_mod347_report()

class l10n_es_aeat_mod347_partner_record(osv.osv):
    """
    Represents a partner record for the 347 model.
    """
    _name = 'l10n.es.aeat.mod347.partner_record'
    _description = 'Partner Record'

    def _name_get(self, cr, uid, ids, field_name, arg, context={}):
        """
        Returns the record name
        """
        result = {}
        for rec in self.browse(cr, uid, ids, context):
            result[rec.id] = rec.partner_vat
        return result

    _columns = {
        # The name it's just an alias of the partner vat
        'name': fields.function(_name_get, method=True, type="char", size="64", string="Name"),

        'report_id': fields.many2one('l10n.es.aeat.mod347.report', 'AEAT 347 Report', ondelete="cascade", select=1),
        'operation_key': fields.selection([
                    ('A', u'A - Adquisiciones de bienes y servicios superiores al límite (1)'),
                    ('B', u'B - Entregas de bienes y servicios superiores al límite (1)'),
                    ('C', u'C - Cobros por cuenta de terceros superiores al límite (3)'),
                    ('D', u'D - Adquisiciones efectuadas por Entidades Públicas (...) superiores al límite (1)'),
                    ('E', u'E - Subvenciones, auxilios y ayudas satisfechas por Ad. Públicas superiores al límite (1)'),
                    ('F', u'F - Ventas agencia viaje'),
                    ('G', u'G - Compras agencia viaje'),
                ], 'Operation Key'),
        'partner_id': fields.many2one('res.partner', 'Partner', required=True),
        'partner_vat': fields.char('VAT number', size=9),
        'representative_vat': fields.char('L.R. VAT number', size=9, help="Legal Representative VAT number"),
        'partner_country_code': fields.char('Country Code', size=2),
        'partner_state_code': fields.char('State Code', size=2),

        'amount': fields.float('Operations amount', digits=(13,2)),
        'cash_amount': fields.float('Received cash amount', digits=(13,2)),
        'real_state_transmissions_amount': fields.float('Real State Transmisions amount', digits=(13,2)),

        'insurance_operation': fields.boolean('Insurance Operation', help="Only for insurance companies. Set to identify insurance operations aside from the rest."),
        'bussiness_real_state_rent': fields.boolean('Bussiness Real State Rent', help="Set to identify real state rent operations aside from the rest. You'll need to fill in the real state info only when you are the one that receives the money."),
        'origin_fiscalyear_id': fields.many2one('account.fiscalyear', 'Origin fiscal year', help="Origin cash operation fiscal year")
    }
    _defaults = {
        'report_id': lambda self, cr, uid, context: context.get('report_id', None),
    }

    def on_change_partner_id(self, cr, uid, ids, partner_id):
        """
        Loads some partner data (country and vat) when the selected partner changes.
        """
        partner_vat = ''
        partner_country_code = ''
        partner_state_code = ''
        if partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id)

            #
            # Get the default invoice address of the partner
            #
            address = None
            address_ids = self.pool.get('res.partner').address_get(cr, uid, [partner.id], ['invoice', 'default'])
            if address_ids.get('invoice'):
                address = self.pool.get('res.partner.address').browse(cr, uid, address_ids.get('invoice'))
            elif address_ids.get('default'):
                address = self.pool.get('res.partner.address').browse(cr, uid, address_ids.get('default'))

            partner_vat = partner.vat and re.match("(ES){0,1}(.*)", partner.vat).groups()[1]
            partner_state_code = address.state_id and address.state_id.code or ''
            partner_country_code = address.country_id and address.country_id.code or ''

        return  {
            'value': {
                    'partner_vat': partner_vat,
                    'partner_country_code': partner_country_code,
                    'partner_state_code': partner_state_code
            }
        }

l10n_es_aeat_mod347_partner_record()


class l10n_es_aeat_mod347_report_add_partner_records(osv.osv):
    """
    Extends the report to add the partner records
    """
    _inherit = 'l10n.es.aeat.mod347.report'
    _columns = {
        'partner_record_ids': fields.one2many('l10n.es.aeat.mod347.partner_record', 'report_id', 'Partner Records',
                            states = {'done': [('readonly', True)]}),
    }
l10n_es_aeat_mod347_report_add_partner_records()


class l10n_es_aeat_mod347_real_state_record(osv.osv):
    """
    Represents a real state record for the 347 model.
    """
    _name = 'l10n.es.aeat.mod347.real_state_record'
    _description = 'Real State Record'


    def _name_get(self, cr, uid, ids, field_name, arg, context={}):
        """
        Returns the record name
        """
        result = {}
        for rec in self.browse(cr, uid, ids, context):
            result[rec.id] = rec.reference
        return result


    _columns = {
        # The name it's just an alias of the reference
        'name': fields.function(_name_get, method=True, type="char", size="64", string="Name"),

        'report_id': fields.many2one('l10n.es.aeat.mod347.report', 'AEAT 347 Report', ondelete="cascade", select=1),

        'partner_id': fields.many2one('res.partner', 'Partner', required=True),
        'partner_vat': fields.char('VAT number', size=32),
        'representative_vat': fields.char('L.R. VAT number', size=32, help="Legal Representative VAT number"),

        'amount': fields.float('Amount', digits=(13,2)),
        'situation': fields.selection([
                    ('1', '1 - Spain but Basque Country and Navarra'),
                    ('2', '2 - Basque Country and Navarra'),
                    ('3', '3 - Spain, without catastral reference'),
                    ('4', '4 - Foreign'),
                ], 'Real state Situation'),
        'reference': fields.char('Catastral Reference', size=25),
        # 'address_id': fields.many2one('res.partner.address', 'Address'),
        'address_type': fields.char('Address type', size=5),
        'address': fields.char('Address', size=50),
        'number_type': fields.selection([
                    ('NUM', 'Number'),
                    ('KM.', 'Kilometer'),
                    ('S/N', 'Without number'),
                ], 'Number type'),
        'number': fields.integer('Number', size=5),
        'number_calification': fields.selection([
                    ('BIS', 'Bis'),
                    ('MOD', 'Mod'),
                    ('DUP', 'Dup'),
                    ('ANT', 'Ant'),
                ], 'Number calification'),
        'block': fields.char('Block', size=3),
        'portal': fields.char('Portal', size=3),
        'stairway': fields.char('Stairway', size=3),
        'floor': fields.char('Floor', size=3),
        'door': fields.char('Door', size=3),
        'complement': fields.char('Complement', size=40, help="Complement (urbanization, industrial park...)"),
        'city': fields.char('City', size=30),
        'township': fields.char('Township', size=30),
        'township_code': fields.char('Township Code', size=5),
        'state_code': fields.char('State Code', size=2),
        'postal_code': fields.char('Postal code', size=5),
    }
    _defaults = {
        'report_id': lambda self, cr, uid, context: context.get('report_id', None),
        'partner_id': lambda self, cr, uid, context: context.get('partner_id', None),
        'partner_vat': lambda self, cr, uid, context: context.get('partner_vat', None),
        'representative_vat': lambda self, cr, uid, context: context.get('representative_vat', None),
    }

    def on_change_partner_id(self, cr, uid, ids, partner_id):
        """
        Loads some partner data (country and vat) when the selected partner changes.
        """
        partner_vat = ''
        if partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id)
            partner_vat = partner.vat and re.match("(ES){0,1}(.*)", partner.vat).groups()[1]

        return  {
            'value': {
                    'partner_vat': partner_vat
            }
        }

l10n_es_aeat_mod347_real_state_record()


class l10n_es_aeat_mod347_report_add_real_state_records(osv.osv):
    """
    Extends the report to add the real state records.
    """
    _inherit = 'l10n.es.aeat.mod347.report'
    _columns = {
        'real_state_record_ids': fields.one2many('l10n.es.aeat.mod347.real_state_record', 'report_id', 'Real State Records',
                            states = {'done': [('readonly', True)]}),
    }
l10n_es_aeat_mod347_report_add_real_state_records()



class l10n_es_aeat_mod347_partner_record_add_real_state_records(osv.osv):
    """
    Extends the partner_records to add the real state records.
    """
    _inherit = 'l10n.es.aeat.mod347.partner_record'


    def _get_real_state_record_ids(self, cr, uid, ids, field_name, args, context=None):
        """
        Get the real state records from this record parent report for this partner.
        """
        if context is None:
            context = {}
        res = {}
        real_state_record_facade = self.pool.get('l10n.es.aeat.mod347.real_state_record')
        for partner_record in self.browse(cr, uid, ids):
            res[partner_record.id] = []
            if partner_record.partner_id:
                res[partner_record.id] = real_state_record_facade.search(cr, uid, [
                            ('report_id', '=', partner_record.report_id.id),
                            ('partner_id', '=', partner_record.partner_id.id),
                        ])
        return res

    def _set_real_state_record_ids(self, cr, uid, id, field_name, values, args=None, context=None):
        """
        Set the real state records from this record parent report for this partner.
        """
        if context is None:
            context = {}
        if values:
            real_state_record_facade = self.pool.get('l10n.es.aeat.mod347.real_state_record')
            for value in values:
                o_action, o_id, o_vals = value
                if o_action == 1:
                    real_state_record_facade.write(cr, uid, [o_id], o_vals)
                elif o_action == 2:
                    real_state_record_facade.unlink(cr, uid, [o_id])
                elif o_action == 0:
                    real_state_record_facade.create(cr, uid, o_vals)
        return True

    _columns = {
        'real_state_record_ids': fields.function(_get_real_state_record_ids,
                    fnct_inv=_set_real_state_record_ids, method=True,
                    obj="l10n.es.aeat.mod347.real_state_record",
                    type="one2many", string='Real State Records', store=False),
    }
l10n_es_aeat_mod347_partner_record_add_real_state_records()



class l10n_es_aeat_mod347_invoice_record(osv.osv):
    """
    Represents an invoice record.
    """

    _name = 'l10n.es.aeat.mod347.invoice_record'
    _description = 'Invoice Record'

    _columns = {
        'partner_record_id': fields.many2one('l10n.es.aeat.mod347.partner_record', 'Partner record', required=True, ondelete="cascade", select=1),
        'invoice_id': fields.many2one('account.invoice', 'Invoice', required=True, ondelete="cascade"),
        'date': fields.date('Date'),
        'amount': fields.float('Amount'),
    }
    _defaults = {
        'partner_record_id': lambda self, cr, uid, context: context.get('partner_record_id', None),
    }
l10n_es_aeat_mod347_invoice_record()


class l10n_es_aeat_mod347_partner_record_add_invoice_records(osv.osv):
    """
    Extends the partner record to add the detail of invoices
    """
    _inherit = 'l10n.es.aeat.mod347.partner_record'

    _columns = {
        'invoice_record_ids': fields.one2many('l10n.es.aeat.mod347.invoice_record', 'partner_record_id', 'Invoice records',
                            states = {'done': [('readonly', True)]}),
    }
l10n_es_aeat_mod347_partner_record_add_invoice_records()



class l10n_es_aeat_mod347_cash_record(osv.osv):
    """
    Represents a payment record.
    """

    _name = 'l10n.es.aeat.mod347.cash_record'
    _description = 'Cash Record'

    _columns = {
        'partner_record_id': fields.many2one('l10n.es.aeat.mod347.partner_record', 'Partner record', required=True , ondelete="cascade", select=1),
        'move_line_id': fields.many2one('account.move.line', 'Account move line', required=True, ondelete="cascade"),
        'date': fields.date('Date'),
        'amount': fields.float('Amount'),
    }
    _defaults = {
        'partner_record_id': lambda self, cr, uid, context: context.get('partner_record_id', None),
    }
l10n_es_aeat_mod347_cash_record()


class l10n_es_aeat_mod347_partner_record_add_cash_records(osv.osv):
    """
    Extends the partner record to add the detail of invoices
    """
    _inherit = 'l10n.es.aeat.mod347.partner_record'

    _columns = {
        'cash_record_ids': fields.one2many('l10n.es.aeat.mod347.cash_record', 'partner_record_id', 'Payment records',
                            states = {'done': [('readonly', True)]}),
    }
l10n_es_aeat_mod347_partner_record_add_cash_records()


