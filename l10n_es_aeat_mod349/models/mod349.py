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
from openerp import models, fields, api, exceptions, _
from openerp.addons.l10n_es_aeat_mod349.models.account_invoice \
    import OPERATION_KEYS

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
NAME_RESTRICTIVE_REGEXP = re.compile(
    r"^[a-zA-Z0-9\sáÁéÉíÍóÓúÚñÑçÇäÄëËïÏüÜöÖ"
    r"àÀèÈìÌòÒùÙâÂêÊîÎôÔûÛ\.,-_&'´\\:;:/]*$", re.UNICODE | re.X)


def _check_valid_string(text_to_check):
    """Checks if string fits with RegExp"""
    if text_to_check and NAME_RESTRICTIVE_REGEXP.match(text_to_check):
        return True
    return False


def _format_partner_vat(partner_vat=None, country=None):
    """Formats VAT to match XXVATNUMBER (where XX is country code)."""
    if country and country.code:
        country_pattern = "[" + country.code + country.code.lower() + "]{2}.*"
        vat_regex = re.compile(country_pattern, re.UNICODE | re.X)
        if partner_vat and not vat_regex.match(partner_vat):
            partner_vat = country.code + partner_vat
    return partner_vat


class Mod349(models.Model):
    _inherit = "l10n.es.aeat.report"
    _name = "l10n.es.aeat.mod349.report"
    _description = "AEAT Model 349 Report"

    @api.one
    @api.depends('partner_record_ids', 'partner_refund_ids',
                 'partner_record_ids.total_operation_amount',
                 'partner_refund_ids.total_operation_amount')
    def _get_report_totals(self):
        self.total_partner_records = len(self.partner_record_ids)
        self.total_partner_records_amount = sum([
            record.total_operation_amount for record in
            self.partner_record_ids])
        self.total_partner_refunds = len(self.partner_refund_ids)
        self.total_partner_refunds_amount = sum([
            refund.total_operation_amount for refund in
            self.partner_refund_ids])

    @api.one
    @api.depends()
    def _get_report_alias(self):
        """Returns an alias as name for the report."""
        self.name = '%s - %s/%s' % (
            self.company_id.name or '', self.fiscalyear_id.name or '',
            self.period_selection or '')

    def _create_349_partner_records(self, invoices, partner, operation_key):
        """creates partner records in 349"""
        rec_obj = self.env['l10n.es.aeat.mod349.partner_record']
        partner_country = partner.country_id
        sum_credit = sum([invoice.cc_amount_untaxed for invoice in invoices
                          if invoice.type not in ('in_refund', 'out_refund')])
        sum_debit = sum([invoice.cc_amount_untaxed for invoice in invoices
                         if invoice.type in ('in_refund', 'out_refund')])
        invoice_created = rec_obj.create(
            {'report_id': self.id,
             'partner_id': partner.id,
             'partner_vat': _format_partner_vat(partner_vat=partner.vat,
                                                country=partner_country),
             'operation_key': operation_key,
             'country_id': partner_country.id or False,
             'total_operation_amount': sum_credit - sum_debit
             })
        # Creation of partner detail lines
        for invoice in invoices:
            detail_obj = self.env['l10n.es.aeat.mod349.partner_record_detail']
            detail_obj.create({'partner_record_id': invoice_created.id,
                               'invoice_id': invoice.id,
                               'amount_untaxed': invoice.cc_amount_untaxed})
        return invoice_created

    def _create_349_refund_records(self, refunds, partner, operation_key):
        """Creates restitution records in 349"""
        partner_detail_obj = self.env[
            'l10n.es.aeat.mod349.partner_record_detail']
        obj = self.env['l10n.es.aeat.mod349.partner_refund']
        obj_detail = self.env['l10n.es.aeat.mod349.partner_refund_detail']
        partner_country = partner.country_id
        record = {}
        for refund in refunds:
            # goes around all refunded invoices
            for origin_inv in refund.origin_invoices_ids:
                if origin_inv.state in ('open', 'paid'):
                    # searches for details of another 349s to restore
                    refund_details = partner_detail_obj.search(
                        [('invoice_id', '=', origin_inv.id)])
                    if refund_details:
                        # creates a dictionary key with partner_record id to
                        # after recover it
                        key = refund_details.partner_record_id
                        if record.get(key, False):
                            record[key].append(refund)
                        else:
                            record[key] = [refund]
                        break
        # recorremos nuestro diccionario y vamos creando registros
        for partner_rec in record:
            record_created = obj.create(
                {'report_id': self.id,
                 'partner_id': partner.id,
                 'partner_vat': _format_partner_vat(
                     partner_vat=partner.vat, country=partner_country),
                 'operation_key': operation_key,
                 'country_id': partner_country.id,
                 'total_operation_amount': partner_rec.total_operation_amount -
                    sum([x.cc_amount_untaxed for x in record[partner_rec]]),
                 'total_origin_amount': partner_rec.total_operation_amount,
                 'period_selection': partner_rec.report_id.period_selection,
                 'month_selection': partner_rec.report_id.month_selection,
                 'fiscalyear_id': partner_rec.report_id.fiscalyear_id.id})
            # Creation of partner detail lines
            for refund in record[partner_rec]:
                obj_detail.create(
                    {'refund_id': record_created.id,
                     'invoice_id': refund.id,
                     'amount_untaxed': refund.cc_amount_untaxed})
        return True

    @api.multi
    def calculate(self):
        """Computes the records in report."""
        partner_obj = self.env['res.partner']
        invoice_obj = self.env['account.invoice']
        for mod349 in self:
            # Remove previous partner records and partner refunds in report
            mod349.partner_record_ids.unlink()
            mod349.partner_refund_ids.unlink()
            # Returns all commercial partners
            partners = partner_obj.with_context(active_test=False).search(
                [('parent_id', '=', False)])
            for partner in partners:
                for op_key in [x[0] for x in OPERATION_KEYS]:
                    # Invoices
                    invoices_total = invoice_obj._get_invoices_by_type(
                        partner, operation_key=op_key,
                        period_selection=mod349.period_selection,
                        fiscalyear=mod349.fiscalyear_id,
                        period_id=[x.id for x in mod349.period_ids],
                        month=mod349.month_selection)
                    # Separates normal invoices from restitution
                    invoices, refunds = \
                        invoices_total.clean_refund_invoices(
                            partner, fiscalyear=mod349.fiscalyear_id,
                            periods=mod349.period_ids,
                            month=mod349.month_selection,
                            period_selection=mod349.period_selection)
                    if invoices:
                        mod349._create_349_partner_records(invoices, partner,
                                                           op_key)
                    if refunds:
                        mod349._create_349_refund_records(refunds, partner,
                                                          op_key)
        return True

    @api.multi
    def _check_report_lines(self):
        """Checks if all the fields of all the report lines
        (partner records and partner refund) are filled
        """
        for item in self:
            # Browse partner record lines to check if
            # all are correct (all fields filled)
            for partner_record in item.partner_record_ids:
                if not partner_record.partner_record_ok:
                    raise exceptions.Warning(
                        _("All partner records fields (country, VAT number) "
                          "must be filled."))
                if partner_record.total_operation_amount < 0:
                    raise exceptions.Warning(
                        _("All amounts must be positives"))
            for partner_record in item.partner_refund_ids:
                if not partner_record.partner_refund_ok:
                    raise exceptions.Warning(
                        _("All partner refunds fields (country, VAT number) "
                          "must be filled."))
                if (partner_record.total_operation_amount < 0 or
                        partner_record.total_origin_amount < 0):
                    raise exceptions.Warning(
                        _("All amounts must be positives"))

    @api.multi
    def _check_names(self):
        """Checks that names are correct (not formed by only one string)"""
        for item in self:
            # Check Full name (contact_name)
            if (not item.contact_name or
                    len(item.contact_name.split(' ')) < 2):
                raise exceptions.Warning(
                    _('Contact name (Full name) must have name and surname'))

    @api.multi
    def _check_restrictive_names(self):
        """Checks if names have not allowed characters and returns a message"""
        for item in self:
            if not _check_valid_string(item.contact_name):
                raise exceptions.Warning(
                    _("Name '%s' have not allowed characters.\nPlease, fix it "
                      "before confirm the report") % item.contact_name)
            # Check partner record partner names
            for partner_record in item.partner_record_ids:
                if not _check_valid_string(partner_record.partner_id.name):
                    raise exceptions.Warning(
                        _("Partner name '%s' in partner records is not valid "
                          "due to incorrect characters") %
                        partner_record.partner_id.name)
            # Check partner refund partner names
            for partner_refund in item.partner_refund_ids:
                if not _check_valid_string(partner_refund.partner_id.name):
                    raise exceptions.Warning(
                        _("Partner name '%s' in refund lines is not valid due "
                          "to incorrect characters") %
                        partner_refund.partner_id.name)

    @api.multi
    def button_confirm(self):
        """Checks if all the fields of the report are correctly filled"""
        self._check_names()
        self._check_report_lines()
        self._check_restrictive_names()
        return super(Mod349, self).button_confirm()

    @api.multi
    def onchange_period_selection(self, period_selection, fiscalyear_id):
        period = False
        if period_selection:
            if period_selection in ['1T', '2T', '3T', '4T']:
                period = self.env['account.period'].search(
                    [('name', 'like', period_selection),
                     ('fiscalyear_id', '=', fiscalyear_id)])
        return {'value': {'period_id': period and period.id}}

    name = fields.Char(compute="_get_report_alias", string="Name")
    period_ids = fields.Many2many(
        comodel_name='account.period', relation='mod349_mod349_period_rel',
        column1='mod349_id', column2='period_ids', string='Periods')
    period_selection = fields.Selection(
        [('0A', '0A - Annual'),
         ('MO', 'MO - Monthly'),
         ('1T', '1T - First Quarter'),
         ('2T', '2T - Second Quarter'),
         ('3T', '3T - Third Quarter'),
         ('4T', '4T - Fourth Quarter')],
        string='Period', required=True, select=1, default='0A',
        states={'confirmed': [('readonly', True)]})
    month_selection = fields.Selection(
        selection=MONTH_MAPPING, string='Month',
        states={'confirmed': [('readonly', True)]})
    frequency_change = fields.Boolean(
        string='Frequency change', states={'confirmed': [('readonly', True)]})
    total_partner_records = fields.Integer(
        compute="_get_report_totals", string="Partners records")
    total_partner_records_amount = fields.Float(
        compute="_get_report_totals", string="Partners records amount")
    total_partner_refunds = fields.Integer(
        compute="_get_report_totals", string="Partners refunds")
    total_partner_refunds_amount = fields.Float(
        compute="_get_report_totals", string="Partners refunds amount")
    partner_record_ids = fields.One2many(
        comodel_name='l10n.es.aeat.mod349.partner_record',
        inverse_name='report_id', string='Partner records', ondelete='cascade',
        states={'confirmed': [('readonly', True)]})
    partner_refund_ids = fields.One2many(
        comodel_name='l10n.es.aeat.mod349.partner_refund',
        inverse_name='report_id', string='Partner refund IDS',
        ondelete='cascade', states={'confirmed': [('readonly', True)]})
    number = fields.Char(default='349')

    def __init__(self, pool, cr):
        self._aeat_number = '349'
        super(Mod349, self).__init__(pool, cr)


class Mod349PartnerRecord(models.Model):
    """AEAT 349 Model - Partner record
    Shows total amount per operation key (grouped) for each partner
    """
    _name = 'l10n.es.aeat.mod349.partner_record'
    _description = 'AEAT 349 Model - Partner record'
    _order = 'operation_key asc'

    @api.one
    @api.depends('partner_vat')
    def get_record_name(self):
        """Returns the record name."""
        self.name = self.partner_vat

    @api.one
    @api.depends('partner_vat', 'country_id', 'total_operation_amount')
    def _check_partner_record_line(self):
        """Checks if all line fields are filled."""
        self.partner_record_ok = bool(self.partner_vat and self.country_id and
                                      self.total_operation_amount)

    @api.multi
    def onchange_format_partner_vat(self, partner_vat, country_id):
        """Formats VAT to match XXVATNUMBER (where XX is country code)"""
        if country_id:
            country = self.env['res.country'].browse(country_id)
            partner_vat = _format_partner_vat(partner_vat=partner_vat,
                                              country=country)
        return {'value': {'partner_vat': partner_vat}}

    report_id = fields.Many2one(
        comodel_name='l10n.es.aeat.mod349.report',
        string='AEAT 349 Report ID', ondelete="cascade")
    name = fields.Char(compute="get_record_name")
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Partner', required=True)
    partner_vat = fields.Char(string='VAT', size=15, select=1)
    country_id = fields.Many2one(comodel_name='res.country', string='Country')
    operation_key = fields.Selection(
        selection=OPERATION_KEYS, string='Operation key', required=True)
    total_operation_amount = fields.Float(string='Total operation amount')
    partner_record_ok = fields.Boolean(
        compute="_check_partner_record_line", string='Partner Record OK',
        help='Checked if partner record is OK')
    record_detail_ids = fields.One2many(
        comodel_name='l10n.es.aeat.mod349.partner_record_detail',
        inverse_name='partner_record_id', string='Partner record detail IDS')


class Mod349PartnerRecordDetail(models.Model):
    """AEAT 349 Model - Partner record detail
    Shows detail lines for each partner record.
    """
    _name = 'l10n.es.aeat.mod349.partner_record_detail'
    _description = 'AEAT 349 Model - Partner record detail'

    partner_record_id = fields.Many2one(
        comodel_name='l10n.es.aeat.mod349.partner_record',
        default=lambda self: self.env.context.get('partner_record_id'),
        string='Partner record', required=True, ondelete='cascade', select=1)
    invoice_id = fields.Many2one(
        comodel_name='account.invoice', string='Invoice', required=True)
    amount_untaxed = fields.Float(string='Amount untaxed')
    date = fields.Date(related='invoice_id.date_invoice', string="Date",
                       readonly=True)


class Mod349PartnerRefund(models.Model):
    _name = 'l10n.es.aeat.mod349.partner_refund'
    _description = 'AEAT 349 Model - Partner refund'
    _order = 'operation_key asc'

    @api.one
    @api.depends('partner_vat', 'country_id', 'total_operation_amount',
                 'total_origin_amount', 'period_selection', 'fiscalyear_id')
    def _check_partner_refund_line(self):
        """Checks if partner refund line have all fields filled."""
        self.partner_refund_ok = bool(
            self.partner_vat and self.country_id and
            self.total_operation_amount >= 0.0 and
            self.total_origin_amount >= 0.0 and
            self.period_selection and self.fiscalyear_id)

    report_id = fields.Many2one(
        comodel_name='l10n.es.aeat.mod349.report', string='AEAT 349 Report ID',
        ondelete="cascade")
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Partner', required=1, select=1)
    partner_vat = fields.Char(string='VAT', size=15)
    operation_key = fields.Selection(
        selection=OPERATION_KEYS, string='Operation key', required=True)
    country_id = fields.Many2one(comodel_name='res.country', string='Country')
    fiscalyear_id = fields.Many2one(
        comodel_name='account.fiscalyear', string='Fiscal year')
    total_operation_amount = fields.Float(string='Total operation amount')
    total_origin_amount = fields.Float(
        string='Original amount', help="Refund original amount")
    partner_refund_ok = fields.Boolean(
        compute="_check_partner_refund_line", string='Partner refund OK',
        help='Checked if refund record is OK')
    period_selection = fields.Selection(
        [('0A', '0A - Annual'),
         ('MO', 'MO - Monthly'),
         ('1T', '1T - First Quarter'),
         ('2T', '2T - Second Quarter'),
         ('3T', '3T - Third Quarter'),
         ('4T', '4T - Fourth Quarter')], 'Period')
    month_selection = fields.Selection(selection=MONTH_MAPPING, string='Month')
    refund_detail_ids = fields.One2many(
        comodel_name='l10n.es.aeat.mod349.partner_refund_detail',
        inverse_name='refund_id', string='Partner refund detail IDS')

    @api.multi
    def onchange_format_partner_vat(self, partner_vat, country_id):
        """Formats VAT to match XXVATNUMBER (where XX is country code)"""
        if country_id:
            country = self.env['res.country'].browse(country_id)
            partner_vat = _format_partner_vat(partner_vat=partner_vat,
                                              country=country)
        return {'value': {'partner_vat': partner_vat}}


class Mod349PartnerRefundDetail(models.Model):
    _name = 'l10n.es.aeat.mod349.partner_refund_detail'
    _description = 'AEAT 349 Model - Partner refund detail'

    refund_id = fields.Many2one(
        comodel_name='l10n.es.aeat.mod349.partner_refund',
        string='Partner refund ID', ondelete="cascade")
    invoice_id = fields.Many2one(
        comodel_name='account.invoice', string='Invoice ID',
        required=True)
    amount_untaxed = fields.Float(string='Amount untaxed')
    date = fields.Date(related='invoice_id.date_invoice', string="Date",
                       readonly=True)
