# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2010 Pexego Sistemas Informáticos. All Rights Reserved
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

__author__ = "Luis Manuel Angueira Blanco (Pexego)"

"""
AEAT 349 model object and detail lines.
"""

import netsvc
import re
from tools.translate import _
from osv import osv, fields

OPERATION_KEY = [
    (False, ''),
    ('E', 'E - Intra-Community supplies'),
    ('A', 'A - Intra-Community acquisition'),
    ('T', 'T - Triangular operations'),
    ('S', 'S - Intra-Community services'),
    ('I', 'I - Intra-Community services acquisitions'),
    ('M', 'M - Intra-Community supplies without taxes'),
    ('H', 'H - Intra-Community supplies without taxes delivered by legal representative'),
]

MONTH_MAPPING = [
    ('01', 'January'),
    ('02', 'February'),
    ('03', 'March'),
    ('04', 'April'),
    ('05', 'May'),
    ('06', 'June'),
    ('07', 'July'),
    ('08', 'August'),
    ('09', 'September'),
    ('10', 'October'),
    ('11', 'November'),
    ('12', 'December'), 
]

MONTH_DATES_MAPPING = {
    '01' : {'date_start' : '%s-01-01', 'date_stop' : '%s-01-31'},
    '02' : {'date_start' : '%s-02-01', 'date_stop' : '%s-02-28'},
    '03' : {'date_start' : '%s-03-01', 'date_stop' : '%s-03-31'},
    '04' : {'date_start' : '%s-04-01', 'date_stop' : '%s-04-30'},
    '05' : {'date_start' : '%s-05-01', 'date_stop' : '%s-05-31'},
    '06' : {'date_start' : '%s-06-01', 'date_stop' : '%s-06-30'},
    '07' : {'date_start' : '%s-07-01', 'date_stop' : '%s-07-31'},
    '08' : {'date_start' : '%s-08-01', 'date_stop' : '%s-08-31'},
    '09' : {'date_start' : '%s-09-01', 'date_stop' : '%s-09-30'},
    '10' : {'date_start' : '%s-10-01', 'date_stop' : '%s-10-31'},
    '11' : {'date_start' : '%s-11-01', 'date_stop' : '%s-11-30'},
    '12' : {'date_start' : '%s-12-01', 'date_stop' : '%s-12-31'},
}


##
## RegExp to check correct strings. Characters allowed
## Numbers 0-9
## Alfabetical Characters a-z (and uppercase)
## Spain 'special' characters ñ,ç (and uppercase)
## Blank spaces
## Punctuation marks and other (\.,-_&'´\:;)
NAME_RESTRICTIVE_REGEXP = re.compile(u"^[a-zA-Z0-9\sáÁéÉíÍóÓúÚñÑçÇäÄëËïÏüÜöÖàÀèÈìÌòÒùÙâÂêÊîÎôÔûÛ\.,-_&'´\:;:/]*$" , re.UNICODE | re.X)

def _check_valid_string(text_to_check):
    """
    Checks if string fits with RegExp
    """
    if text_to_check and NAME_RESTRICTIVE_REGEXP.match(text_to_check):
        return True
    return False


class account_fiscal_position(osv.osv):
    """
    Inheritance of Account fiscal position to add field 'include_in_mod349'.
    This fields let us map fiscal position, taxes and accounts to create an AEAT 349 Report
    """
    _inherit = 'account.fiscal.position'

    _columns = {
        'intracommunity_operations' : fields.boolean('Intra-Community operations'),
    }

account_fiscal_position()


class account_invoice(osv.osv):
    """
    Inheritance of account invoce to add some fields
    """
    _inherit = 'account.invoice'

    def _get_invoices_by_type(self, cr, uid, partner_id, operation_key,
        fiscalyear_id=None, period_id=None, month=None, period_selection=None):
        """
        Returns invoices ids by type (supplier/customer) for a fiscalyear/period/month
        """
        assert period_selection, _('There is no period selected')

        ## Set type of invoice
        type = ['in_invoice', 'out_invoice', 'in_refund', 'out_refund']

        fiscalyear_obj = self.pool.get('account.fiscalyear').browse(cr, uid, fiscalyear_id)
        search_dict = [
            ('partner_id', '=', partner_id),
            ('state', 'in', ['open', 'paid']),
            ('type', 'in', type),
            ('operation_key', '=', operation_key)]

        ##
        ## Invoices by fiscalyear (Annual)
        if period_selection == '0A':
            if not fiscalyear_id:
                raise osv.except_osv(_('Error'), _('Cannot get invoices.\nThere is no fiscalyear selected'))

            search_dict.append(('period_id', 'in', [period.id for period in fiscalyear_obj.period_ids if period.special == False]))

        ##
        ## Invoices by period
        elif period_selection in ['1T', '2T', '3T', '4T']:
            if not period_id:
                raise osv.except_osv(_('Error'), _('Cannot get invoices.\nThere is no period selected'))
            
            search_dict.append(('period_id', '=', period_id))

        ##
        ## Invoices by month
        else:
            year = fiscalyear_obj.code[:4]
            if not month and not fiscalyear_id:
                raise osv.except_osv(_('Error'), _('Cannot get invoices.\nThere is no month and/or fiscalyear selected'))

            search_dict.append(('date_invoice', '>=', MONTH_DATES_MAPPING[month]['date_start'] % year))

            if month == '02':
                #checks if year is leap to can search by last February date in database
                if int(year) % 4 == 0 and (int(year) % 100 != 0 or int(year) % 400 == 0):
                    search_dict.append(('date_invoice', '<=', "%s-02-29" % year))
                else:
                   search_dict.append(('date_invoice', '<=', MONTH_DATES_MAPPING[month]['date_stop'] % year))
            else:
                search_dict.append(('date_invoice', '<=', MONTH_DATES_MAPPING[month]['date_stop'] % year))

        return self.search(cr, uid, search_dict)

    def clean_refund_invoices(self, cr, uid, ids, partner_id, fiscalyear_id=None, period_id=None, month=None, period_selection=None):
        """separates restitution invoices"""
        invoice_lines = []
        restitution_lines = []
        fiscalyear_obj = self.pool.get('account.fiscalyear').browse(cr, uid, fiscalyear_id)

        for refund in self.browse(cr, uid, ids):
            if refund.type in ['in_refund', 'out_refund']:
                if not refund.origin_invoices_ids:
                    invoice_lines.append(refund.id)
                    continue
                for origin_line in refund.origin_invoices_ids:
                    if origin_line.state in ['open', 'paid'] and origin_line.partner_id.id == partner_id:
                        if period_selection == '0A':
                            if origin_line.period_id.id not in [period.id for period in fiscalyear_obj.period_ids if not period.special]:
                                restitution_lines.append(refund.id)
                                break
                            else:
                                invoice_lines.append(refund.id)
                                break
                        elif period_selection in ['1T', '2T', '3T', '4T']:
                            if origin_line.period_id.id != period_id:
                                restitution_lines.append(refund.id)
                                break
                            else:
                                invoice_lines.append(refund.id)
                                break
                        else:
                            if origin_line.date_invoice < MONTH_DATES_MAPPING[month]['date_start'] % fiscalyear_obj.code[:4]:
                                restitution_lines.append(refund.id)
                                break
                            else:
                                invoice_lines.append(refund.id)
                                break
            else:
                invoice_lines.append(refund.id)

        return invoice_lines, restitution_lines

    def on_change_fiscal_position(self, cr, uid, ids, fiscal_position, type, context=None):
        """
        Suggest an operation key when fiscal position changes
        """
        if context is None:
            context = {}

        res = {'value' : {'operation_key' : None}}
        if fiscal_position and type:
            if self.pool.get('account.fiscal.position').browse(cr, uid, fiscal_position).intracommunity_operations:
                if type == 'out_invoice':
                    res = {'value' : {'operation_key' : 'E'}}   ## Set to supplies when type is 'out_invoice' (Customer invoice)
                else:
                    res = {'value' : {'operation_key' : 'A'}}   ## Set to acquisition when type is 'in_invoice' (Supplier invoice)
                    
        return res


    def onchange_partner_id(self, cr, uid, ids, type, partner_id, date_invoice=False, payment_term=False, partner_bank=False):
        """
        Inheritance to extend method and return operation key
        """
        ##
        ## Get original data from onchange method
        res = super(account_invoice, self).onchange_partner_id(cr, uid, ids, type, partner_id, date_invoice=date_invoice, payment_term=payment_term, partner_bank=partner_bank)

        ##
        ## Get operation key for current record
        operation_key_dict = self.on_change_fiscal_position(cr, uid, ids, 
            fiscal_position=res['value']['fiscal_position'], type=type)

        ##
        ## Add operation key to result
        if operation_key_dict['value'] and \
            operation_key_dict['value']['operation_key']:
            res['value']['operation_key'] = operation_key_dict['value']['operation_key']
        else:
            res['value']['operation_key'] = False

        return res



    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}

        if vals.get('fiscal_position') and vals.get('type') and not vals.get('operation_key'):
            if self.pool.get('account.fiscal.position').browse(cr, uid, vals.get('fiscal_position')).intracommunity_operations:
                if vals.get('type') == 'out_invoice':
                    vals['operation_key'] = 'E'
                else:
                    vals['operation_key'] = 'A'
            
        return super(account_invoice, self).create(cr, uid, vals, context)

    _columns = {
        'operation_key' : fields.selection(OPERATION_KEY, 'Operation key')
    }
    
account_invoice()


class l10n_es_aeat_mod349_report(osv.osv):
    """
    AEAT 349 Model
    """
    _name = 'l10n.es.aeat.mod349.report'
    _description = 'AEAT 349 Model'

    def _get_report_alias(self, cr, uid, ids, field_name, args, context=None):
        """
        Returns an alias as name for the report
        """
        if context is None:
            context = {}
        res = {}

        for item in self.browse(cr, uid, ids):
            res[item.id] = '%s - %s/%s' % (
                item.company_id and item.company_id.name or '',
                item.fiscalyear_id and item.fiscalyear_id.name or '',
                item.period_selection or '')
            
        return res


    def _check_names(self, cr, uid, ids, context=None):
        """
        Checks that names are correct (not formed by only one string)
        """
        if context is None:
            context = {}        

        for item in self.browse(cr, uid, ids):
            ## Check company name and title
            if not item.company_id.partner_id or \
                not item.company_id.partner_id.title:
                return {
                    'warning' : {
                        'title' : _('Company without Title'),
                        'message' : _('Company has no company title.\nThis may cause some problems when trying to import on AEAT help program')
                        }
                    }
                    
            ## Check Full name (contact_name)
            if not item.contact_name or \
                len(item.contact_name.split(' ')) < 2:
                raise osv.except_osv(_('Error!'), _('Contact name (Full name) must have name and surname'))

                
    def _check_report_lines(self, cr, uid, ids, context=None):
        """
        Checks if all the fields of all the report lines (partner records and partner refund) are filled
        """
        if context is None:
            context = {}
            
        for item in self.browse(cr, uid, ids, context):
            ## Browse partner record lines to check if all are correct (all fields filled)
            for partner_record in item.partner_record_ids:
                if not partner_record.partner_record_ok:
                    raise osv.except_osv(_('Error!'), _("All partner records fields (country, VAT number) must be filled"))
                if partner_record.total_operation_amount < 0:
                    raise osv.except_osv(_('Error!'), _("All amounts must be positives"))
                
            for partner_record in item.partner_refund_ids:
                if not partner_record.partner_refund_ok:
                    raise osv.except_osv(_('Error!'), _("All partner refunds fields (country, VAT number) must be filled"))
                if partner_record.total_operation_amount < 0 or partner_record.total_origin_amount < 0:
                    raise osv.except_osv(_('Error!'), _("All amounts must be positives"))

        return True


    def _check_restrictive_names(self, cr, uid, ids, context=None):
        """
        Checks if names have not allowed characters and returns a message
        """
        if context is None:
            context = {}

        mod349_obj = self.browse(cr, uid, ids and ids[0], context)
        if not _check_valid_string(mod349_obj.contact_name):
            raise osv.except_osv(_('Error!'),
                _("Name '%s' have not allowed characters.\nPlease, fix it before confirm the report") % mod349_obj.contact_name)

        ##
        ## Check partner record partner names
        for partner_record in mod349_obj.partner_record_ids:
            if not _check_valid_string(partner_record.partner_id.name):
                raise osv.except_osv(_("Error!"),
                    _("Partner name '%s' in partner records is not valid due to incorrect characters") % partner_record.partner_id.name)

        ##
        ## Check partner refund partner names
        for partner_refund in mod349_obj.partner_refund_ids:
            if not _check_valid_string(partner_refund.partner_id.name):
                raise osv.except_osv(_("Error!"),
                    _("Partner name '%s' in refund lines is not valid due to incorrect characters") % partner_refund.partner_id.name)



    def _get_report_totals(self, cr, uid, ids, name, args, context=None):
        """
        Gets statistics for current report
        """
        if context is None:
            context = {}
        res = {}
        
        for report in self.browse(cr, uid, ids, context=context):
            res[report.id] = {
                'total_partner_records': len(report.partner_record_ids),
                'total_partner_records_amount': sum([record.total_operation_amount for record in report.partner_record_ids]) or 0.0,
                'total_partner_refunds': len(report.partner_refund_ids),
                'total_partner_refunds_amount': sum([refund.total_operation_amount for refund in report.partner_refund_ids]) or 0.0,
            }

        return res


    def _check_report(self, cr, uid, ids, context):
        """
        Checks if all the fields of the report are filled
        """
        if context is None:
            context = {}

        self._check_names(cr, uid, ids, context)
        self._check_report_lines(cr, uid, ids, context)
        self._check_restrictive_names(cr, uid, ids, context)


    def wkf_action_recover(self, cr, uid, ids, context=None):
        """ Workflow: action recover """
        self.write(cr, uid, ids, {'state': 'draft'})
        wf_service = netsvc.LocalService("workflow")
        for item_id in ids:
            wf_service.trg_create(uid, 'l10n.es.aeat.mod349.report', item_id, cr)
        return True


    def wkf_confirm(self, cr, uid, ids, context=None):
        """ Workflow : confirm """
        if context is None:
            context = {}

        self._check_report(cr, uid, ids, context)
        self.write(cr, uid, ids, {'state':'confirmed'})
        return True


    def onchange_period_selection(self, cr, uid, ids, period_selection, fiscalyear_id, context=None):
        if context is None:
            context = {}

        period_id = None
        if period_selection:
            if period_selection in ['1T', '2T', '3T', '4T']:
                period_id = self.pool.get('account.period').search(cr, uid, [
                    ('name', 'like', period_selection),
                    ('fiscalyear_id', '=', fiscalyear_id)])
                    
        return {'value' : { 'period_id' : period_id and period_id[0] or None}}


    _columns = {
        ## The name is just an alias
        'name' : fields.function(_get_report_alias, type='char', string='Name', method=True),
            
        'company_id' : fields.many2one('res.company', 'Company', required=True, states={'confirmed':[('readonly',True)]}),
        'fiscalyear_id' : fields.many2one('account.fiscalyear', 'Fiscalyear', required=True, select=1, states={'confirmed':[('readonly',True)]}),
        'period_id' : fields.many2one('account.period', 'Period', states={'confirmed':[('readonly',True)]}),
        'period_selection' : fields.selection([
                ('0A', '0A - Annual'),
                ('MO', 'MO - Monthly'),
                ('1T', '1T - First Quarter'),
                ('2T', '2T - Second Quarter'),
                ('3T', '3T - Third Quarter'),
                ('4T', '4T - Fourth Quarter'),
            ], 'Period', required=True, select=1,
            states={'confirmed':[('readonly',True)]}),

        'month_selection' : fields.selection(MONTH_MAPPING, 'Month', states={'confirmed':[('readonly',True)]}),

        'type': fields.selection([
            ('N','Normal'),
            ('C','Complementary'),
            ('S','Substitutive')], 'Statement Type',
            states={'calculated':[('required',True)],'confirmed':[('readonly',True)]}),
        'number': fields.char('Declaration Number', size=13, states={'calculated':[('required',True)],'confirmed':[('readonly',True)]}),
        'previous_number' : fields.char('Previous Declaration Number', size=13, states={'confirmed':[('readonly',True)]}),
        'frequency_change' : fields.boolean('Frequency change', states={'confirmed':[('readonly',True)]}),
        'support_type': fields.selection([
            ('C','DVD'),
            ('T','Telematics')], 'Support Type',
            states={'calculated':[('required',True)],'confirmed':[('readonly',True)]}),

        ##
        ## Identification
        ##
        'company_vat': fields.char('VAT number', size=9, states={'calculated':[('required',True)],'confirmed':[('readonly',True)]}),
        'representative_vat': fields.char('L.R. VAT number', size=9, help="Legal Representative VAT number.\nMust have name and surname.", states={'calculated':[('required',True)],'confirmed':[('readonly',True)]}),
        'contact_name': fields.char("Full Name", size=40, help="Must have name and surname.", states={'calculated':[('required',True)],'confirmed':[('readonly',True)]}),
        'contact_phone': fields.char("Phone", size=9, states={'calculated':[('required',True)],'confirmed':[('readonly',True)]}),
        
        ##
        ## TOTALS
        ##
        'total_partner_records' : fields.function(_get_report_totals, string="Partners records", method=True,
            type='integer', multi="report_totals_multi"),
        'total_partner_records_amount' : fields.function(_get_report_totals, string="Partners records amount",
            method=True, type='float', multi="report_totals_multi"),
        'total_partner_refunds' : fields.function(_get_report_totals, string="Partners refunds", method=True,
            type='integer', multi="report_totals_multi"),
        'total_partner_refunds_amount' : fields.function(_get_report_totals, string="Partners refunds amount", method=True,
            type='float', multi="report_totals_multi"),

        'state' : fields.selection([
            ('draft', 'Draft'),                     
            ('calculated', 'Calculated'),
            ('confirmed', 'Confirmed'),
            ('done', 'Done'),
            ('canceled', 'Canceled')
            ], 'State', readonly=True),

    }

    _defaults = {
        'company_id': lambda self, cr, uid, context:
            self.pool.get('res.users').browse(cr, uid, uid, context).company_id and
            self.pool.get('res.users').browse(cr, uid, uid, context).company_id.id,
            
        'state' : lambda *a: 'draft',
        'type' : lambda *a: 'N',

        'number' : lambda *a: '349',        ## AEAT brings number (previous number), so take default value as 349 (need to be changed)
    }
    
l10n_es_aeat_mod349_report()


class l10n_es_aeat_mod349_partner_record(osv.osv):
    """
    AEAT 349 Model - Partner record
    Shows total amount per operation key (grouped) for each partner
    """
    _name = 'l10n.es.aeat.mod349.partner_record'
    _description = 'AEAT 349 Model - Partner record'
    _order = 'operation_key asc'


    def get_record_name(self, cr, uid, ids, field_name, args, context={}):
        """
        Returns the record name
        """
        result = {}
        for rec in self.browse(cr, uid, ids, context):
            result[rec.id] = rec.partner_vat
        return result


    def _check_partner_record_line(self, cr, uid, ids, name, args, context=None):
        """
        Checks if all line fields are filled
        """
        if context is None:
            context = {}
            
        res = {}
        for item in self.browse(cr, uid, ids):
            if item.partner_vat and \
                item.country_id and \
                item.total_operation_amount:
                res[item.id] = True
            else:
                res[item.id] = False
                        
        return res

    def onchange_format_partner_vat(self, cr, uid, ids, partner_vat, country_id):
        """
        Formats VAT to match XXVATNUMBER (where XX is country code)
        """
        if country_id:
            country_code = self.pool.get('res.country').browse(cr, uid, country_id).code
            country_pattern ="["+country_code+country_code.lower()+"]{2}.*"
            vat_regex = re.compile(country_pattern, re.UNICODE | re.X)

            if partner_vat and not vat_regex.match(partner_vat):
                partner_vat = country_code + partner_vat

        return {'value' : {'partner_vat' : partner_vat}}

    _columns = {
        'report_id' : fields.many2one('l10n.es.aeat.mod349.report', 'AEAT 349 Report ID'),

        # The name it's just an alias of the partner vat
        'name': fields.function(get_record_name, method=True, type="char", size="64", string="Name"),
        'partner_id' : fields.many2one('res.partner', 'Partner', required=True),
        'partner_vat' : fields.char('VAT', size=15, select=1),
        'country_id' : fields.many2one('res.country', 'Country'),
        'operation_key' : fields.selection(OPERATION_KEY, 'Operation key', required=True),

        'total_operation_amount' : fields.float('Total operation amount'),

        'partner_record_ok' : fields.function(_check_partner_record_line, method=True,
            string='Partner Record OK', help='Checked if Partner record is OK'),
    }

l10n_es_aeat_mod349_partner_record()


class l10n_es_aeat_mod349_report_add_partner_records(osv.osv):
    """
    Inheritance of 'l10n.es.aeat.mod349.report' to add a relation between partner record and report
    """
    _inherit = 'l10n.es.aeat.mod349.report'

    _columns = {
        'partner_record_ids' : fields.one2many('l10n.es.aeat.mod349.partner_record', 'report_id', 'Partner records',
            ondelete='cascade', states={'confirmed':[('readonly',True)]}),
    }

l10n_es_aeat_mod349_report_add_partner_records()


class l10n_es_aeat_mod349_partner_record_detail(osv.osv):
    """
    AEAT 349 Model - Partner record detail
    Shows detail lines for each partner record.
    """
    _name = 'l10n.es.aeat.mod349.partner_record_detail'
    _description = 'AEAT 349 Model - Partner record detail'

    _columns = {
        'partner_record_id' : fields.many2one('l10n.es.aeat.mod349.partner_record', 'Partner record', required=True, ondelete='cascade', select=1),

        'invoice_id' : fields.many2one('account.invoice', 'Invoice'),
        'amount_untaxed' : fields.float('Amount untaxed'),                 
        'date' : fields.related('invoice_id', 'date_invoice', type="date", string="Date", readonly=True),
    }

    _defaults = {
        'partner_record_id' : lambda self, cr, uid, context : context.get('partner_record_id', None),
    }

l10n_es_aeat_mod349_partner_record_detail()


class l10n_es_aeat_mod349_partner_record_add_partner_record_details(osv.osv):
    """
    Inheritance of 'l10n.es.aeat.mod349.partner_record' to add a relation between
    partner record and partner record details
    """
    _inherit = 'l10n.es.aeat.mod349.partner_record'

    _columns = {
        'record_detail_ids' : fields.one2many('l10n.es.aeat.mod349.partner_record_detail', 'partner_record_id', 'Partner record detail IDS', ondelete='cascade'),
    }
    
l10n_es_aeat_mod349_partner_record_add_partner_record_details()


class l10n_es_aeat_mod349_partner_refund(osv.osv):
    
    _name = 'l10n.es.aeat.mod349.partner_refund'
    _description = 'AEAT 349 Model - Partner refund'
    _order = 'operation_key asc'


    def _check_partner_refund_line(self, cr, uid, ids, field_name, args, context=None):
        """
        Checks if partner refund line have all fields filled
        """
        if context is None:
            context = {}

        res = {}
        for item in self.browse(cr, uid, ids, context):
            if item.partner_vat and \
                item.country_id and \
                item.total_operation_amount >= 0.0 and \
                item.total_origin_amount >= 0.0 and \
                item.period_selection and \
                item.fiscalyear_id:
                res[item.id] = True
            else:
                res[item.id] = False

        return res

    _columns = {
        'report_id' : fields.many2one('l10n.es.aeat.mod349.report', 'AEAT 349 Report ID'),

        'partner_id' : fields.many2one('res.partner', 'Partner', required=1, select=1),
        'partner_vat' : fields.char('VAT', size=15),
        'operation_key' : fields.selection(OPERATION_KEY, 'Operation key', required=True),
        'country_id' : fields.many2one('res.country', 'Country'),
        'fiscalyear_id' : fields.many2one('account.fiscalyear', 'Fiscalyear'),
        'total_operation_amount' : fields.float('Total operation amount'),
        'total_origin_amount' : fields.float('Original amount', help="Refund original amount"),
        'partner_refund_ok' : fields.function(_check_partner_refund_line, method=True,
            string='Partner refund OK', help='Checked if Refund record is OK'),
        'period_selection' : fields.selection([
                ('0A', '0A - Annual'),
                ('MO', 'MO - Monthly'),
                ('1T', '1T - First Quarter'),
                ('2T', '2T - Second Quarter'),
                ('3T', '3T - Third Quarter'),
                ('4T', '4T - Fourth Quarter')
            ], 'Period'),
        'month_selection' : fields.selection(MONTH_MAPPING, 'Month')
    }

    _defaults = {
        'partner_refund_ok' : lambda *a: 0,
    }

    def onchange_format_partner_vat(self, cr, uid, ids, partner_vat, country_id):
        """
        Formats VAT to match XXVATNUMBER (where XX is country code)
        """
        if country_id:
            country_code = self.pool.get('res.country').browse(cr, uid, country_id).code
            country_pattern ="["+country_code+country_code.lower()+"]{2}.*"
            vat_regex = re.compile(country_pattern, re.UNICODE | re.X)

            if partner_vat and not vat_regex.match(partner_vat):
                partner_vat = country_code + partner_vat

        return {'value' : {'partner_vat' : partner_vat}}

l10n_es_aeat_mod349_partner_refund()


class l10n_es_aeat_mod349_partner_record_add_partner_refund(osv.osv):
    """
    Inheritance of 'l10n.es.aeat.mod349.report' to add a relation between partner refund and report
    """
    _inherit = 'l10n.es.aeat.mod349.report'

    _columns = {
        'partner_refund_ids' : fields.one2many('l10n.es.aeat.mod349.partner_refund', 'report_id', 'Partner refund IDS',
            ondelete='cascade', states={'confirmed':[('readonly',True)]}),
    }
    
l10n_es_aeat_mod349_partner_record_add_partner_refund()


class l10n_es_aeat_mod349_partner_refund_detail(osv.osv):

    _name = 'l10n.es.aeat.mod349.partner_refund_detail'
    _description = 'AEAT 349 Model - Partner refund detail'

    _columns = {
        'refund_id' : fields.many2one('l10n.es.aeat.mod349.partner_refund', 'Partner refund ID'),

        'invoice_id' : fields.many2one('account.invoice', 'Invoice ID'),
        'amount_untaxed' : fields.float('Amount untaxed'),
        'date' : fields.related('invoice_id', 'date_invoice', type="date", string="Date", readonly=True)
    }

l10n_es_aeat_mod349_partner_refund_detail()


class l10n_es_aeat_mod349_partner_refund_add_partner_refund_detail(osv.osv):
    """
    Inheritance of 'l10n.es.aeat.mod349.partner_refund' to add a relation between partner refund and partner refund detail
    """
    _inherit = 'l10n.es.aeat.mod349.partner_refund'

    _columns = {
        'refund_detail_ids' : fields.one2many('l10n.es.aeat.mod349.partner_refund_detail', 'refund_id', 'Partner refund detail IDS', ondelete='cascade'),
    }

l10n_es_aeat_mod349_partner_refund_add_partner_refund_detail()
