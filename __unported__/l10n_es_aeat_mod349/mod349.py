# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C)
#        2004-2011: Pexego Sistemas Informáticos. (http://pexego.es)
#        2013:      Top Consultant Software Creations S.L.
#                   (http://www.topconsultant.es/)
#        2014:      Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                   Pedro M. Baeza <pedro.baeza@serviciosbaeza.com> 
#
#    Autores originales: Luis Manuel Angueira Blanco (Pexego)
#                        Omar Castiñeira Saavedra(omar@pexego.es)
#    Migración OpenERP 7.0: Ignacio Martínez y Miguel López.
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
import re
from openerp.tools.translate import _
from openerp.osv import fields, orm
from openerp.addons.l10n_es_aeat_mod349.account_invoice import OPERATION_KEYS

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

# TODO: Quitarlo de aquí y pasarlo a l10n_es_aeat con sustituciones
NAME_RESTRICTIVE_REGEXP = re.compile(u"^[a-zA-Z0-9\sáÁéÉíÍóÓúÚñÑçÇäÄëËïÏüÜöÖ"
                                     u"àÀèÈìÌòÒùÙâÂêÊîÎôÔûÛ\.,-_&'´\:;:/]*$",
                                     re.UNICODE | re.X)

def _check_valid_string(text_to_check):
    """
    Checks if string fits with RegExp
    """
    if text_to_check and NAME_RESTRICTIVE_REGEXP.match(text_to_check):
        return True
    return False

def _format_partner_vat(cr, uid, partner_vat=None, country=None,
                      context=None):
    """Formats VAT to match XXVATNUMBER (where XX is country code)."""
    if country:
        country_pattern = "[" + country.code + country.code.lower() + "]{2}.*"
        vat_regex = re.compile(country_pattern, re.UNICODE | re.X)
        if partner_vat and not vat_regex.match(partner_vat):
            partner_vat = country.code + partner_vat
    return partner_vat


class Mod349(orm.Model):
    _inherit = "l10n.es.aeat.report"
    _name = "l10n.es.aeat.mod349.report"
    _description = "AEAT Model 349 Report"

    ### FUNCTIONS ###
    def _get_report_totals(self, cr, uid, ids, name, args, context=None):
        res = {}
        for report in self.browse(cr, uid, ids, context=context):
            res[report.id] = {
                'total_partner_records': len(report.partner_record_ids),
                'total_partner_records_amount':
                            sum([record.total_operation_amount for record in
                                 report.partner_record_ids]) or 0.0,
                'total_partner_refunds': len(report.partner_refund_ids),
                'total_partner_refunds_amount':
                            sum([refund.total_operation_amount for refund in
                                 report.partner_refund_ids]) or 0.0,
            }
        return res

    def _get_report_alias(self, cr, uid, ids, field_name, args,
                          context=None):
        """Returns an alias as name for the report."""
        res = {}
        for item in self.browse(cr, uid, ids, context=context):
            res[item.id] = '%s - %s/%s' % (
                item.company_id and item.company_id.name or '',
                item.fiscalyear_id and item.fiscalyear_id.name or '',
                item.period_selection or '')
        return res

    def _create_349_partner_records(self, cr, uid, ids, report_id,
                                           partner_obj, operation_key,
                                           context=None):
        """creates partner records in 349"""
        invoices_ids = self.pool['account.invoice'].browse(cr, uid, ids,
                                                           context=context)
        obj = self.pool['l10n.es.aeat.mod349.partner_record']
        partner_country = partner_obj.country_id
        invoice_created = obj.create(cr, uid, {
            'report_id': report_id,
            'partner_id': partner_obj.id,
            'partner_vat': _format_partner_vat(cr, uid,
                                               partner_vat=partner_obj.vat,
                                               country=partner_country),
            'operation_key': operation_key,
            'country_id': partner_country.id or False,
            'total_operation_amount': sum([invoice.cc_amount_untaxed for
                                            invoice in invoices_ids if
                                            invoice.type not in
                                            ('in_refund', 'out_refund')]) -
                                               sum([invoice.cc_amount_untaxed
                                                    for invoice in invoices_ids
                                                    if invoice.type in
                                                    ('in_refund',
                                                     'out_refund')])
        })
        ### Creation of partner detail lines
        for invoice in invoices_ids:
            detail_obj = self.pool['l10n.es.aeat.mod349.partner_record_detail']
            detail_obj.create(cr, uid,
                              {'partner_record_id': invoice_created,
                               'invoice_id': invoice.id,
                               'amount_untaxed': invoice.cc_amount_untaxed})
        return invoice_created

    def _create_349_refund_records(self, cr, uid, ids, report_id,
                                    partner_obj, operation_key, context=None):
        """Creates restitution records in 349"""
        refunds = self.pool['account.invoice'].browse(cr, uid, ids)
        refundpol = self.pool['l10n.es.aeat.mod349.partner_record_detail']
        refund_obj = self.pool['l10n.es.aeat.mod349.partner_record']
        obj = self.pool['l10n.es.aeat.mod349.partner_refund']
        obj_detail = self.pool['l10n.es.aeat.mod349.partner_refund_detail']
        partner_country = [address.country_id for address in
                           partner_obj.address if address.type ==
                           'invoice' and address.country_id]
        if not partner_country:
            partner_country = [address.country_id for
                               address in partner_obj.address
                               if address.type == 'default' and
                               address.country_id]
        partner_country = partner_country and partner_country[0] or False
        record = {}
        for invoice in refunds:
            #goes around all refunded invoices
            for origin_inv in invoice.origin_invoices_ids:
                if origin_inv.state in ['open', 'paid']:
                    # searches for details of another 349s to restor
                    refund_detail = refundpol.search(cr, uid,
                                                     [('invoice_id', '=',
                                                       origin_inv.id)])
                    valid_refund_details = refund_detail
                    for detail in refundpol.browse(cr, uid, refund_detail):
                        if not detail.partner_record_id.report_id:
                            valid_refund_details.remove(detail.id)
                    if valid_refund_details:
                        rd = refundpol.browse(cr, uid, valid_refund_details[0])
                        #creates a dictionary key with partner_record id to
                        #after recover it
                        key = str(rd.partner_record_id.id)
                        #separates restitutive invoices and nomal, refund
                        #invoices of correct period
                        if record.get(key):
                            record[key].append(invoice)
                            #NOTE: Two or more refunded invoices declared in
                            #different 349s isn't implemented
                            break
                        else:
                            record[key] = [invoice]
                            #NOTE: Two or more refunded invoices declared in
                            #different 349s isn't implemented
                            break
        #recorremos nuestro diccionario y vamos creando registros
        for line in record:
            partner_rec = refund_obj.browse(cr, uid, int(line),
                                            context=context)
            record_created = obj.create(cr, uid, {
                'report_id': report_id,
                'partner_id': partner_obj.id,
                'partner_vat': _format_partner_vat(cr, uid,
                                                   partner_vat=partner_obj.vat,
                                                   country=partner_country,
                                                   context=context),
                'operation_key': operation_key,
                'country_id': partner_country and partner_country.id or False,
                'total_operation_amount':  partner_rec.total_operation_amount \
                    - sum([x.cc_amount_untaxed for x in record[line]]),
                'total_origin_amount': partner_rec.total_operation_amount,
                'period_selection': partner_rec.report_id.period_selection,
                'month_selection': partner_rec.report_id.month_selection,
                'fiscalyear_id': partner_rec.report_id.fiscalyear_id.id
            }, context=context)
            ### Creation of partner detail lines
            for invoice in record[line]:
                obj_detail.create(cr, uid, {
                    'refund_id': record_created,
                    'invoice_id': invoice.id,
                    'amount_untaxed': invoice.cc_amount_untaxed
                }, context=context)
        return True

    def calculate(self, cr, uid, ids, context=None):
        """Computes the records in report."""
        partner_obj = self.pool['res.partner']
        invoice_obj = self.pool['account.invoice']
        report_obj = self.pool['l10n.es.aeat.mod349.report']
        partner_record_obj = self.pool['l10n.es.aeat.mod349.partner_record']
        partner_refund_obj = self.pool['l10n.es.aeat.mod349.partner_refund']
        for mod349 in self.browse(cr, uid, ids, context=context):
            ## Remove previous partner records and partner refunds in report
            partner_record_obj.unlink(cr, uid, [record.id for record in
                                                mod349.partner_record_ids],
                                      context=context)
            partner_refund_obj.unlink(cr, uid, [refund.id for refund in
                                                mod349.partner_refund_ids],
                                      context=context)
            # Returns all partners
            # TODO: Problema: Si se ha desactivado el partner, pero tiene
            # facturas, no saldrán en el informe
            partner_ids = partner_obj.search(cr, uid, [], context=context)
            for partner_id in partner_ids:
                for op_key in [x[0] for x in OPERATION_KEYS]:
                    ## Invoices
                    invoice_ids = invoice_obj._get_invoices_by_type(cr, uid,
                                partner_id,
                                operation_key=op_key,
                                period_selection=mod349.period_selection,
                                fiscalyear_id=mod349.fiscalyear_id.id,
                                period_id=[x.id for x in mod349.period_ids],
                                month=mod349.month_selection, context=context)
                    # Separates normal invoices from restitution
                    invoice_ids, refunds_ids = invoice_obj.\
                        clean_refund_invoices(cr, uid, invoice_ids, partner_id,
                                  fiscalyear_id=mod349.fiscalyear_id.id,
                                  period_id=[x.id for x in mod349.period_ids],
                                  month=mod349.month_selection,
                                  period_selection=mod349.period_selection,
                                  context=context)
                    if invoice_ids or refunds_ids:
                        partner = partner_obj.browse(cr, uid, partner_id,
                                                     context=context)
                    if invoice_ids:
                        self._create_349_partner_records(cr, uid,
                                            invoice_ids, mod349.id, partner,
                                            op_key, context=context)
                    if refunds_ids:
                        self._create_349_refund_records(cr, uid,
                                            refunds_ids, mod349.id, partner,
                                            op_key, context=context)
        return True

    def _check_report_lines(self, cr, uid, ids, context=None):
        """
        Checks if all the fields of all the report lines
        (partner records and partner refund) are filled
        """
        for item in self.browse(cr, uid, ids, context):
            ## Browse partner record lines to check if
            ## all are correct (all fields filled)
            for partner_record in item.partner_record_ids:
                if not partner_record.partner_record_ok:
                    raise orm.except_orm(_('Error!'),
                        _("All partner records fields (country, VAT number) "
                          "must be filled."))
                if partner_record.total_operation_amount < 0:
                    raise orm.except_orm(_('Error!'),
                                         _("All amounts must be positives"))
            for partner_record in item.partner_refund_ids:
                if not partner_record.partner_refund_ok:
                    raise orm.except_orm(_('Error!'),
                        _("All partner refunds fields (country, VAT number) "
                          "must be filled."))
                if partner_record.total_operation_amount < 0 or \
                                partner_record.total_origin_amount < 0:
                    raise orm.except_orm(_('Error!'),
                                         _("All amounts must be positives"))
        return True

    def _check_names(self, cr, uid, ids, context=None):
        """
        Checks that names are correct (not formed by only one string)
        """
        for item in self.browse(cr, uid, ids, context=context):
            ## Check company name and title
            if not item.company_id.partner_id or \
                not item.company_id.partner_id.title:
                return {
                    'warning': {
                        'title': _('Company without Title'),
                        'message': _('Company has no company title.\nThis ' +
                                     'may cause some problems when trying ' +
                                     'to import on AEAT help program')
                        }
                    }
            ## Check Full name (contact_name)
            if not item.contact_name or \
                len(item.contact_name.split(' ')) < 2:
                raise orm.except_orm(_('Error!'),
                                     _('Contact name (Full name) must have ' +
                                       'name and surname'))

    def _check_restrictive_names(self, cr, uid, ids, context=None):
        """
        Checks if names have not allowed characters and returns a message
        """
        mod349_obj = self.browse(cr, uid, ids and ids[0], context)
        if not _check_valid_string(mod349_obj.contact_name):
            raise orm.except_orm(_('Error!'),
                _("Name '%s' have not allowed characters.\nPlease, fix it "
                  "before confirm the report") % mod349_obj.contact_name)
        ## Check partner record partner names
        for partner_record in mod349_obj.partner_record_ids:
            if not _check_valid_string(partner_record.partner_id.name):
                raise orm.except_orm(_("Error!"),
                    _("Partner name '%s' in partner records is not valid "
                      "due to incorrect characters") %
                                     partner_record.partner_id.name)
        ## Check partner refund partner names
        for partner_refund in mod349_obj.partner_refund_ids:
            if not _check_valid_string(partner_refund.partner_id.name):
                raise orm.except_orm(_("Error!"),
                    _("Partner name '%s' in refund lines is not valid due "
                      "to incorrect characters") %
                                     partner_refund.partner_id.name)

    def button_confirm(self, cr, uid, ids, context=None):
        """
        Checks if all the fields of the report are correctly filled
        """
        self._check_names(cr, uid, ids, context)
        self._check_report_lines(cr, uid, ids, context)
        self._check_restrictive_names(cr, uid, ids, context)
        return super(Mod349, self).button_confirm(cr, uid, ids,
                                                  context=context)

    def onchange_period_selection(self, cr, uid, ids, period_selection,
                                  fiscalyear_id, context=None):
        period_id = None
        if period_selection:
            if period_selection in ['1T', '2T', '3T', '4T']:
                period_id = self.pool.get('account.period').search(cr, uid, [
                    ('name', 'like', period_selection),
                    ('fiscalyear_id', '=', fiscalyear_id)], context=context)
        return {'value': {'period_id': period_id and period_id[0] or False}}

    _columns = {
        ## The name is just an alias
        'name': fields.function(_get_report_alias, type="char",
                                string="Name", method=True),
        'period_ids': fields.many2many('account.period',
                                       'mod349_mod349_period_rel',
                                       'mod349_id', 'period_ids', 'Periods'),
        'period_selection': fields.selection([
                ('0A', '0A - Annual'),
                ('MO', 'MO - Monthly'),
                ('1T', '1T - First Quarter'),
                ('2T', '2T - Second Quarter'),
                ('3T', '3T - Third Quarter'),
                ('4T', '4T - Fourth Quarter')
            ], 'Period', required=True, select=1,
            states={'confirmed': [('readonly', True)]}),
        'month_selection': fields.selection(MONTH_MAPPING, 'Month',
                                states={'confirmed': [('readonly', True)]}),
        'frequency_change': fields.boolean('Frequency change',
                                states={'confirmed': [('readonly', True)]}),
        ## Identification
        'contact_name': fields.char("Full Name", size=40,
                                help="Must have name and surname.",
                                states={'calculated': [('required', True)],
                                        'confirmed': [('readonly', True)]}),
        'contact_phone': fields.char("Phone", size=9,
                            states={'calculated': [('required', True)],
                                    'confirmed': [('readonly', True)]}),
        ## TOTALS
        'total_partner_records': fields.function(_get_report_totals,
                            string="Partners records", method=True,
                            type='integer', multi="report_totals_multi"),
        'total_partner_records_amount': fields.function(_get_report_totals,
                            string="Partners records amount", method=True,
                            type='float', multi="report_totals_multi"),
        'total_partner_refunds': fields.function(_get_report_totals,
                            string="Partners refunds", method=True,
                            type='integer', multi="report_totals_multi"),
        'total_partner_refunds_amount': fields.function(_get_report_totals,
                            string="Partners refunds amount", method=True,
                            type='float', multi="report_totals_multi"),
        # LISTADOS
        'partner_record_ids': fields.one2many(
                            'l10n.es.aeat.mod349.partner_record',
                            'report_id', 'Partner records', ondelete='cascade',
                            states={'confirmed': [('readonly', True)]}),
        'partner_refund_ids': fields.one2many(
                        'l10n.es.aeat.mod349.partner_refund',
                        'report_id', 'Partner refund IDS', ondelete='cascade',
                        states={'confirmed': [('readonly', True)]}),
    }
    _defaults = {
        'period_selection': '0A',
        'type': 'N',
        'number': '349',
    }


class Mod349PartnerRecord(orm.Model):
    """
    AEAT 349 Model - Partner record
    Shows total amount per operation key (grouped) for each partner
    """
    _name = 'l10n.es.aeat.mod349.partner_record'
    _description = 'AEAT 349 Model - Partner record'
    _order = 'operation_key asc'

    def get_record_name(self, cr, uid, ids, field_name, args, context={}):
        """Returns the record name."""
        result = {}
        for rec in self.browse(cr, uid, ids, context):
            result[rec.id] = rec.partner_vat
        return result

    def _check_partner_record_line(self, cr, uid, ids,
                                   name, args, context=None):
        """Checks if all line fields are filled."""
        res = {}
        for item in self.browse(cr, uid, ids, context=context):
            res[item.id] = bool(item.partner_vat and item.country_id and
                                item.total_operation_amount)
        return res

    def onchange_format_partner_vat(self, cr, uid, ids,
                                    partner_vat, country_id, context=None):
        """
        Formats VAT to match XXVATNUMBER (where XX is country code)
        """
        if country_id:
            country_obj = self.pool['res.country']
            country = country_obj.browse(cr, uid, country_id, context=context)
            partner_vat = _format_partner_vat(cr, uid, partner_vat=partner_vat,
                                              country=country)
        return {'value': {'partner_vat': partner_vat}}

    _columns = {
        'report_id': fields.many2one('l10n.es.aeat.mod349.report',
                                     'AEAT 349 Report ID'),
        # The name it's just an alias of the partner vat
        'name': fields.function(get_record_name, method=True, type="char",
                                string="Name"),
        'partner_id': fields.many2one('res.partner', 'Partner', required=True),
        'partner_vat': fields.char('VAT', size=15, select=1),
        'country_id': fields.many2one('res.country', 'Country'),
        'operation_key': fields.selection(OPERATION_KEYS, 'Operation key',
                                          required=True),
        'total_operation_amount': fields.float('Total operation amount'),
        'partner_record_ok': fields.function(_check_partner_record_line,
                                    method=True, string='Partner Record OK',
                                    help='Checked if partner record is OK'),
        'record_detail_ids': fields.one2many(
                            'l10n.es.aeat.mod349.partner_record_detail',
                            'partner_record_id', 'Partner record detail IDS',
                            ondelete='cascade'),
    }


class Mod349PartnerRecordDetail(orm.Model):
    """
    AEAT 349 Model - Partner record detail
    Shows detail lines for each partner record.
    """
    _name = 'l10n.es.aeat.mod349.partner_record_detail'
    _description = 'AEAT 349 Model - Partner record detail'

    _columns = {
        'partner_record_id': fields.many2one(
                                        'l10n.es.aeat.mod349.partner_record',
                                        'Partner record', required=True,
                                        ondelete='cascade', select=1),
        'invoice_id': fields.many2one('account.invoice', 'Invoice'),
        'amount_untaxed': fields.float('Amount untaxed'),
        'date': fields.related('invoice_id', 'date_invoice', type="date",
                               string="Date", readonly=True),
    }

    _defaults = {
        'partner_record_id': lambda self, cr, uid, context:
                                        context.get('partner_record_id', None),
    }


class Mod349PartnerRefund(orm.Model):
    _name = 'l10n.es.aeat.mod349.partner_refund'
    _description = 'AEAT 349 Model - Partner refund'
    _order = 'operation_key asc'

    def _check_partner_refund_line(self, cr, uid, ids,
                                   field_name, args, context=None):
        """
        Checks if partner refund line have all fields filled
        """
        res = {}
        for item in self.browse(cr, uid, ids, context):
            res[item.id] = bool(item.partner_vat and item.country_id and
                                item.total_operation_amount >= 0.0 and
                                item.total_origin_amount >= 0.0 and
                                item.period_selection and item.fiscalyear_id)
        return res

    _columns = {
        'report_id': fields.many2one('l10n.es.aeat.mod349.report',
                                     'AEAT 349 Report ID'),
        'partner_id': fields.many2one('res.partner', 'Partner', required=1,
                                      select=1),
        'partner_vat': fields.char('VAT', size=15),
        'operation_key': fields.selection(OPERATION_KEYS, 'Operation key',
                                          required=True),
        'country_id': fields.many2one('res.country', 'Country'),
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal year'),
        'total_operation_amount': fields.float('Total operation amount'),
        'total_origin_amount': fields.float('Original amount',
                                            help="Refund original amount"),
        'partner_refund_ok': fields.function(_check_partner_refund_line,
                                     method=True, string='Partner refund OK',
                                     help='Checked if refund record is OK'),
        'period_selection': fields.selection([
                ('0A', '0A - Annual'),
                ('MO', 'MO - Monthly'),
                ('1T', '1T - First Quarter'),
                ('2T', '2T - Second Quarter'),
                ('3T', '3T - Third Quarter'),
                ('4T', '4T - Fourth Quarter')
            ], 'Period'),
        'month_selection': fields.selection(MONTH_MAPPING, 'Month'),
        'refund_detail_ids': fields.one2many(
                                'l10n.es.aeat.mod349.partner_refund_detail',
                                'refund_id', 'Partner refund detail IDS',
                                ondelete='cascade'),
    }

    _defaults = {
        'partner_refund_ok': 0,
    }

    def onchange_format_partner_vat(self, cr, uid, ids,
                                    partner_vat, country_id, context=None):
        """Formats VAT to match XXVATNUMBER (where XX is country code)"""
        if country_id:
            country_obj = self.pool['res.country']
            country = country_obj.browse(cr, uid, country_id, context=context)
            partner_vat = _format_partner_vat(cr, uid, partner_vat=partner_vat,
                                              country=country)
        return {'value': {'partner_vat': partner_vat}}


class Mod349PartnerRefundDetail(orm.Model):
    _name = 'l10n.es.aeat.mod349.partner_refund_detail'
    _description = 'AEAT 349 Model - Partner refund detail'

    _columns = {
        'refund_id': fields.many2one('l10n.es.aeat.mod349.partner_refund',
                                     'Partner refund ID'),
        'invoice_id': fields.many2one('account.invoice', 'Invoice ID'),
        'amount_untaxed': fields.float('Amount untaxed'),
        'date': fields.related('invoice_id', 'date_invoice',
                               type="date", string="Date", readonly=True)
    }
