# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2011
#        Pexego Sistemas Informáticos. (http://pexego.es) All Rights Reserved
#
#    Copyright (C) 2012
#        NaN·Tic  (http://www.nan-tic.com) All Rights Reserved
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

__author__ = "Luis Manuel Angueira Blanco (Pexego)"

import re
from osv import osv, fields
from tools.translate import _

class l10n_es_aeat_mod347_report(osv.osv):

    _inherit = "l10n.es.aeat.report"
    _name = "l10n.es.aeat.mod347.report"
    _description = "AEAT 347 Report"
    _rec_name = "number"

    def button_calculate(self, cr, uid, ids, context=None):
        if not context:
            context = {}

        calculate_obj = self. pool.get('l10n.es.aeat.mod347.calculate_records')
        calculate_obj._wkf_calculate_records(cr, uid, ids, context)

        return True

    def button_recalculate(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        calculate_obj = self. pool.get('l10n.es.aeat.mod347.calculate_records')
        calculate_obj._calculate_records(cr, uid, ids, context)

        return True

    def button_export(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        export_obj = self.pool.get("l10n.es.aeat.mod347.export_to_boe")
        export_obj._export_boe_file(cr, uid, ids, self.browse(cr, uid, ids and ids[0]))

        return True

    def _get_totals(self, cr, uid, ids, name, args, context=None):
        """
        Calculates the total_* fields from the line values.
        """
        if context is None:
            context = {}

        res = {}

        for report in self.browse(cr, uid, ids, context=context):
            res[report.id] = {
                'total_partner_records': len(report.partner_record_ids),
                'total_amount' : sum([record.amount for record in report.partner_record_ids]) or 0.0,
                'total_cash_amount' : sum([record.cash_amount for record in report.partner_record_ids]) or 0.0,
                'total_real_state_transmissions_amount' : sum([record.real_state_transmissions_amount for record in report.partner_record_ids]) or 0.,
                'total_real_state_records' : len(report.real_state_record_ids),
                'total_real_state_amount' : sum([record.amount for record in report.real_state_record_ids]) or 0,
            }

        return res

    _columns = {
        'contact_name': fields.char("Full Name", size=40),
        'contact_phone': fields.char("Phone", size=9),
        'group_by_cif': fields.boolean('Group by cif', states={'done':[('readonly',True)]}),

        ##
        ## Limits
        'operations_limit': fields.float('Invoiced Limit (1)', digits=(13,2), help="The declaration will include partners with the total of operations over this limit"),
        'received_cash_limit': fields.float('Received cash Limit (2)', digits=(13,2), help="The declaration will show the total of cash operations over this limit"),
        'charges_obtp_limit': fields.float('Charges on behalf of third parties Limit (3)', digits=(13,2), help="The declaration will include partners from which we received payments, on behalf of third parties, over this limit"),

        ##
        ## Totals
        'total_partner_records': fields.function(_get_totals, string="Partners records", method=True, type='integer', multi="totals_multi"),
        'total_amount': fields.function(_get_totals, string="Amount", method=True, type='float', multi="totals_multi"),
        'total_cash_amount': fields.function(_get_totals, string="Cash Amount", method=True, type='float', multi="totals_multi"),
        'total_real_state_transmissions_amount': fields.function(_get_totals, string="Real Estate Transmissions Amount", method=True, type='float', multi="totals_multi"),
        'total_real_state_records': fields.function(_get_totals, string="Real estate records", method=True, type='integer', multi="totals_multi"),
        'total_real_state_amount': fields.function(_get_totals, string="Real Estate Amount", method=True, type='float', multi="totals_multi"),

    }
    _defaults = {
        ##
        ## Default limits
        'operations_limit': lambda *args: 3005.06,
        'charges_obtp_limit': lambda *args: 300.51,
        'received_cash_limit': lambda *args: 6000.00,

        ##
        ## AEAT brings number (previous number), so take defautl value as 349 (need to be changed)
        'number' : lambda *a: '347'
    }

    def _check_report_lines(self, cr, uid, ids, context=None):
        """checks report lines"""
        if context is None: context = {}

        for item in self.browse(cr, uid, ids, context):
            ## Browse partner record lines to check if all are correct (all fields filled)
            for partner_record in item.partner_record_ids:
                if not partner_record.partner_state_code:
                    raise osv.except_osv(_('Error!'), _("All partner state code field must be filled.\nPartner: %s (%s)") % ( partner_record.partner_id.name, partner_record.partner_id.id ) )
                if not partner_record.partner_vat and not partner_record.community_vat:
                    raise osv.except_osv(_('Error!'), _("All partner vat number field must be filled.\nPartner: %s (%s)") % ( partner_record.partner_id.name, partner_record.partner_id.id ) )
                if partner_record.partner_state_code and not partner_record.partner_state_code.isdigit():
                    raise osv.except_osv(_('Error!'), _("All partner state code field must be numeric.\nPartner: %s (%s)") % ( partner_record.partner_id.name, partner_record.partner_id.id ) )

            for real_state_record in item.real_state_record_ids:
                if not real_state_record.state_code:
                    raise osv.except_osv(_('Error!'), _("All real estate records state code field must be filled."))

        return True

    def check_report(self, cr, uid, ids, context=None):
        """Different check out in report"""
        if context is None: context = {}

        self._check_report_lines(cr, uid, ids, context)

        return True

    def action_confirm(self, cr, uid, ids, context=None):
        """set to done the report and check its records"""
        if context is None: context = {}

        self.check_report(cr, uid, ids, context)
        self.write(cr, uid, ids, {'state': 'done'})

        return True

l10n_es_aeat_mod347_report()


class l10n_es_aeat_mod347_partner_record(osv.osv):
    """
    Represents a partner record for the 347 model.
    """
    _name = 'l10n.es.aeat.mod347.partner_record'
    _description = 'Partner Record'
    _rec_name = "partner_vat"

    def _get_quarter_totals(self, cr, uid, ids, field_name, arg, context = None):

        if context is None:
            context={}

        result = {}
        for record  in self.browse(cr, uid, ids, context):
            result[record.id] ={
            'first_quarter':0,
            'first_quarter_real_state_transmission_amount':0,
            'second_quarter': 0,
            'second_quarter_real_state_transmission_amount':0,
            'third_quarter': 0,
            'third_quarter_real_state_transmission_amount':0,
            'fourth_quarter': 0,
            'fourth_quarter_real_state_transmission_amount':0,
            }
            for invoice in record.invoice_record_ids:
                if invoice.invoice_id.period_id.quarter == 'first':
                    result[record.id]['first_quarter'] += invoice.amount
                elif invoice.invoice_id.period_id.quarter == 'second':
                    result[record.id]['second_quarter'] += invoice.amount
                elif invoice.invoice_id.period_id.quarter == 'third':
                    result[record.id]['third_quarter'] += invoice.amount
                elif invoice.invoice_id.period_id.quarter == 'fourth':
                    result[record.id]['fourth_quarter'] += invoice.amount

        return result

    def _get_lines( self, cr, uid, ids, context ):
        invoice_record_obj = self.pool.get('l10n.es.aeat.mod347.invoice_record')

        res = []
        for invoice_record in invoice_record_obj.browse(cr, uid, ids, context):
            res.append( invoice_record.partner_record_id.id )
        return list(set(res))


    _columns = {
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
        'community_vat': fields.char('Community vat number', size=17, help="VAT number for professionals established in other state member without national VAT"),
        'partner_country_code': fields.char('Country Code', size=2),
        'partner_state_code': fields.char('State Code', size=2),
        'first_quarter': fields.function(_get_quarter_totals, string="First Quarter",
                method=True, type='float', multi="quarter_multi",digits=(13,2),
                store= {
                    'l10n.es.aeat.mod347.invoice_record': (_get_lines, ['amount'] , 10 )
                }),
        'first_quarter_real_state_transmission_amount':fields.function(_get_quarter_totals, string="First Quarter Real Estate Transmission Amount",
                method=True, type='float', multi="quarter_multi" ,digits=(13,2),
                store= {
                    'l10n.es.aeat.mod347.invoice_record': (_get_lines, ['amount'] , 10 )
                }
                ),
        'second_quarter': fields.function(_get_quarter_totals, string="Second Quarter", method=True,
                type='float', multi="quarter_multi", digits=(13,2),
                store= {
                    'l10n.es.aeat.mod347.invoice_record': (_get_lines, ['amount'] , 10 )
                }),
        'second_quarter_real_state_transmission_amount':fields.function(_get_quarter_totals, string="Second Quarter Real Estate Transmission Amount",
                method=True, type='float', multi="quarter_multi",digits=(13,2), store= {
                    'l10n.es.aeat.mod347.invoice_record': (_get_lines, ['amount'] , 10 )
                }),
        'third_quarter': fields.function(_get_quarter_totals, string="Third Quarter", method=True, type='float',
                multi="quarter_multi",digits=(13,2), store= {
                    'l10n.es.aeat.mod347.invoice_record': (_get_lines, ['amount'] , 10 )
                }),
        'third_quarter_real_state_transmission_amount':fields.function(_get_quarter_totals, string="Third Quarter Real Estate Transmission Amount",
                method=True, type='float', multi="quarter_multi",digits=(13,2), store= {
                    'l10n.es.aeat.mod347.invoice_record': (_get_lines, ['amount'] , 10 )
                } ),
        'fourth_quarter': fields.function(_get_quarter_totals, string="Fourth Quarter",
                method=True, type='float', multi="quarter_multi",digits=(13,2), store= {
                    'l10n.es.aeat.mod347.invoice_record': (_get_lines, ['amount'] , 10 )
                }),
        'fourth_quarter_real_state_transmission_amount':fields.function(_get_quarter_totals, string="Fourth Quarter Real Estate Transmossion Amount",
                method=True, type='float', multi="quarter_multi",digits=(13,2), store= {
                    'l10n.es.aeat.mod347.invoice_record': (_get_lines, ['amount'] , 10 )
                }),
        'amount': fields.float('Operations amount', digits=(13,2)),
        'cash_amount': fields.float('Received cash amount', digits=(13,2)),
        'real_state_transmissions_amount': fields.float('Real Estate Transmisions amount', digits=(13,2)),

        'insurance_operation': fields.boolean('Insurance Operation', help="Only for insurance companies. Set to identify insurance operations aside from the rest."),
        'cash_basis_operation': fields.boolean('Cash Basis Operation', help="Only for cash basis operations. Set to identify cash basis operations aside from the rest."),
        'tax_person_operation': fields.boolean('Taxable Person Operation', help="Only for taxable person operations. Set to identify taxable person operations aside from the rest."),
        'related_goods_operation': fields.boolean('Related Goods Operation', help="Only for related goods operations. Set to identify related goods operations aside from the rest."),
        'bussiness_real_state_rent': fields.boolean('Bussiness Real Estate Rent', help="Set to identify real estate rent operations aside from the rest. You'll need to fill in the real estate info only when you are the one that receives the money."),
        'origin_fiscalyear_id': fields.many2one('account.fiscalyear', 'Origin fiscal year', help="Origin cash operation fiscal year"),
        'invoice_record_ids': fields.one2many('l10n.es.aeat.mod347.invoice_record', 'partner_record_id', 'Invoice records',
                                                      states = {'done': [('readonly', True)]}),

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
    Represents a real estate record for the 347 model.
    """
    _name = 'l10n.es.aeat.mod347.real_state_record'
    _description = 'Real Estate Record'
    _rec_name = "reference"

    _columns = {
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
                ], 'Real estate Situation'),
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
    Extends the report to add the real estate records.
    """
    _inherit = 'l10n.es.aeat.mod347.report'
    _columns = {
        'real_state_record_ids': fields.one2many('l10n.es.aeat.mod347.real_state_record', 'report_id', 'Real Estate Records',
                            states = {'done': [('readonly', True)]}),
    }
l10n_es_aeat_mod347_report_add_real_state_records()


class l10n_es_aeat_mod347_partner_record_add_real_state_records(osv.osv):
    """
    Extends the partner_records to add the real estate records.
    """
    _inherit = 'l10n.es.aeat.mod347.partner_record'


    def _get_real_state_record_ids(self, cr, uid, ids, field_name, args, context=None):
        """
        Get the real estate records from this record parent report for this partner.
        """
        if context is None:
            context = {}
        res = {}
        real_state_record_obj = self.pool.get('l10n.es.aeat.mod347.real_state_record')
        for partner_record in self.browse(cr, uid, ids):
            res[partner_record.id] = []
            if partner_record.partner_id:
                res[partner_record.id] = real_state_record_obj.search(cr, uid, [
                            ('report_id', '=', partner_record.report_id.id),
                            ('partner_id', '=', partner_record.partner_id.id),
                        ])
        return res

    def _set_real_state_record_ids(self, cr, uid, id, field_name, values, args=None, context=None):
        """
        Set the real estate records from this record parent report for this partner.
        """
        if context is None:
            context = {}
        if values:
            real_state_record_obj = self.pool.get('l10n.es.aeat.mod347.real_state_record')
            for value in values:
                o_action, o_id, o_vals = value
                if o_action == 1:
                    real_state_record_obj.write(cr, uid, [o_id], o_vals)
                elif o_action == 2:
                    real_state_record_obj.unlink(cr, uid, [o_id])
                elif o_action == 0:
                    real_state_record_obj.create(cr, uid, o_vals)
        return True

    _columns = {
        'real_state_record_ids': fields.function(_get_real_state_record_ids,
                    fnct_inv=_set_real_state_record_ids, method=True,
                    obj="l10n.es.aeat.mod347.real_state_record",
                    type="one2many", string='Real Estate Records', store=False),
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



