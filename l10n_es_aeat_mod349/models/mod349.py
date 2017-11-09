# -*- coding: utf-8 -*-
# Copyright 2004-2011 - Pexego Sistemas Informáticos. (http://pexego.es)
# Copyright 2013 - Top Consultant Software Creations S.L.
#                - (http://www.topconsultant.es/)
# Copyright 2014 - Serv. Tecnol. Avanzados
#                - Pedro M. Baeza (http://www.serviciosbaeza.com)
# Copyright 2016 - Tecnativa - Angel Moya <odoo@tecnativa.com>
# Copyright 2017 - Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re
from odoo import models, fields, api, exceptions, _
from .account_invoice import OPERATION_KEYS


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
    _period_yearly = True
    _aeat_number = '349'

    def _default_export_config_id(self):
        try:
            return self.env.ref(
                'l10n_es_aeat_mod349.aeat_mod349_main_export_config').id
        except ValueError:
            return self.env['aeat.model.export.config']

    export_config_id = fields.Many2one(
        comodel_name='aeat.model.export.config', oldname='export_config',
        string="Export configuration", default=_default_export_config_id,
    )
    frequency_change = fields.Boolean(
        string='Frequency change', states={'confirmed': [('readonly', True)]})
    total_partner_records = fields.Integer(
        compute="_compute_report_regular_totals", string="Partners records",
    )
    total_partner_records_amount = fields.Float(
        compute="_compute_report_regular_totals",
        string="Partners records amount",
    )
    total_partner_refunds = fields.Integer(
        compute="_compute_report_refund_totals", string="Partners refunds",
    )
    total_partner_refunds_amount = fields.Float(
        compute="_compute_report_refund_totals",
        string="Partners refunds amount",
    )
    partner_record_ids = fields.One2many(
        comodel_name='l10n.es.aeat.mod349.partner_record',
        inverse_name='report_id', string='Partner records', ondelete='cascade',
        states={'confirmed': [('readonly', True)]},
    )
    partner_refund_ids = fields.One2many(
        comodel_name='l10n.es.aeat.mod349.partner_refund',
        inverse_name='report_id', string='Partner refund IDS',
        ondelete='cascade', states={'confirmed': [('readonly', True)]},
    )
    number = fields.Char(default='349')

    @api.multi
    @api.depends('partner_record_ids',
                 'partner_record_ids.total_operation_amount')
    def _compute_report_regular_totals(self):
        for report in self:
            report.total_partner_records = len(report.partner_record_ids)
            report.total_partner_records_amount = sum(
                report.mapped('partner_record_ids.total_operation_amount')
            )

    @api.multi
    @api.depends('partner_refund_ids',
                 'partner_refund_ids.total_operation_amount')
    def _compute_report_refund_totals(self):
        for report in self:
            report.total_partner_refunds = len(report.partner_refund_ids)
            report.total_partner_refunds_amount = sum(
                report.mapped('partner_refund_ids.total_operation_amount')
            )

    def _create_349_partner_records(self, invoices, partner, operation_key):
        """creates partner records in 349"""
        rec_obj = self.env['l10n.es.aeat.mod349.partner_record']
        partner_country = partner.country_id
        sum_credit = sum([invoice.amount_untaxed_signed for invoice in invoices
                          if invoice.type not in ('in_refund', 'out_refund')])
        sum_debit = sum([invoice.amount_untaxed_signed for invoice in invoices
                         if invoice.type in ('in_refund', 'out_refund')])
        invoice_created = rec_obj.create(
            {'report_id': self.id,
             'partner_id': partner.id,
             'partner_vat': _format_partner_vat(partner_vat=partner.vat,
                                                country=partner_country),
             'operation_key': operation_key,
             'country_id': partner_country.id or False,
             'total_operation_amount': sum_credit + sum_debit
             })
        # Creation of partner detail lines
        for invoice in invoices:
            detail_obj = self.env['l10n.es.aeat.mod349.partner_record_detail']
            detail_obj.create({'partner_record_id': invoice_created.id,
                               'invoice_id': invoice.id,
                               'amount_untaxed': invoice.amount_untaxed_signed}
                              )
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
            for origin_inv in refund.origin_invoice_ids:
                if origin_inv.state in ('open', 'paid'):
                    # searches for details of another 349s to restore
                    refund_details = partner_detail_obj.search([
                        ('invoice_id', '=', origin_inv.id),
                    ], limit=1)
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
            record_created = obj.create({
                'report_id': self.id,
                'partner_id': partner.id,
                'partner_vat': _format_partner_vat(
                    partner_vat=partner.vat, country=partner_country
                ),
                'operation_key': operation_key,
                'country_id': partner_country.id,
                'total_operation_amount': (
                    partner_rec.total_operation_amount - sum(
                        [x.amount_untaxed_signed for x in record[partner_rec]]
                    )
                ),
                'total_origin_amount': partner_rec.total_operation_amount,
                'period_type': partner_rec.report_id.period_type,
                'year': partner_rec.report_id.year,
            })
            # Creation of partner detail lines
            for refund in record[partner_rec]:
                obj_detail.create(
                    {'refund_id': record_created.id,
                     'invoice_id': refund.id,
                     'amount_untaxed': refund.amount_untaxed_signed})
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
                        date_start=mod349.date_start,
                        date_end=mod349.date_end)
                    # Separates normal invoices from restitution
                    invoices, refunds = \
                        invoices_total.clean_refund_invoices(
                            partner,
                            date_start=mod349.date_start,
                            date_end=mod349.date_end,)
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
    def button_confirm(self):
        """Checks if all the fields of the report are correctly filled"""
        self._check_names()
        self._check_report_lines()
        return super(Mod349, self).button_confirm()


class Mod349PartnerRecord(models.Model):
    """AEAT 349 Model - Partner record
    Shows total amount per operation key (grouped) for each partner
    """
    _name = 'l10n.es.aeat.mod349.partner_record'
    _description = 'AEAT 349 Model - Partner record'
    _order = 'operation_key asc'
    _rec_name = "partner_vat"

    @api.multi
    @api.depends('partner_vat', 'country_id', 'total_operation_amount')
    def _compute_partner_record_ok(self):
        """Checks if all line fields are filled."""
        for record in self:
            record.partner_record_ok = (bool(
                record.partner_vat and record.country_id and
                record.total_operation_amount
            ))

    report_id = fields.Many2one(
        comodel_name='l10n.es.aeat.mod349.report',
        string='AEAT 349 Report ID', ondelete="cascade",
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Partner', required=True,
    )
    partner_vat = fields.Char(string='VAT', size=15, index=True)
    country_id = fields.Many2one(comodel_name='res.country', string='Country')
    operation_key = fields.Selection(
        selection=OPERATION_KEYS, string='Operation key', required=True,
    )
    total_operation_amount = fields.Float(string='Total operation amount')
    partner_record_ok = fields.Boolean(
        compute="_compute_partner_record_ok", string='Partner Record OK',
        help='Checked if partner record is OK',
    )
    record_detail_ids = fields.One2many(
        comodel_name='l10n.es.aeat.mod349.partner_record_detail',
        inverse_name='partner_record_id', string='Partner record detail IDS',
    )

    @api.multi
    def onchange_format_partner_vat(self, partner_vat, country_id):
        """Formats VAT to match XXVATNUMBER (where XX is country code)"""
        if country_id:
            country = self.env['res.country'].browse(country_id)
            partner_vat = _format_partner_vat(partner_vat=partner_vat,
                                              country=country)
        return {'value': {'partner_vat': partner_vat}}


class Mod349PartnerRecordDetail(models.Model):
    """AEAT 349 Model - Partner record detail
    Shows detail lines for each partner record.
    """
    _name = 'l10n.es.aeat.mod349.partner_record_detail'
    _description = 'AEAT 349 Model - Partner record detail'

    partner_record_id = fields.Many2one(
        comodel_name='l10n.es.aeat.mod349.partner_record',
        default=lambda self: self.env.context.get('partner_record_id'),
        string='Partner record', required=True, ondelete='cascade', index=True)
    invoice_id = fields.Many2one(
        comodel_name='account.invoice', string='Invoice', required=True)
    amount_untaxed = fields.Float(string='Amount untaxed')
    date = fields.Date(related='invoice_id.date_invoice', string="Date",
                       readonly=True)


class Mod349PartnerRefund(models.Model):
    _name = 'l10n.es.aeat.mod349.partner_refund'
    _description = 'AEAT 349 Model - Partner refund'
    _order = 'operation_key asc'

    def get_period_type_selection(self):
        report_obj = self.env['l10n.es.aeat.mod349.report']
        return report_obj.get_period_type_selection()

    report_id = fields.Many2one(
        comodel_name='l10n.es.aeat.mod349.report', string='AEAT 349 Report ID',
        ondelete="cascade")
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Partner', required=1, index=True)
    partner_vat = fields.Char(string='VAT', size=15)
    operation_key = fields.Selection(
        selection=OPERATION_KEYS, string='Operation key', required=True)
    country_id = fields.Many2one(comodel_name='res.country', string='Country')
    total_operation_amount = fields.Float(string='Total operation amount')
    total_origin_amount = fields.Float(
        string='Original amount', help="Refund original amount")
    partner_refund_ok = fields.Boolean(
        compute="_compute_partner_refund_ok", string='Partner refund OK',
        help='Checked if refund record is OK',
    )
    period_type = fields.Selection(
        selection='get_period_type_selection', string="Period type",
    )
    year = fields.Integer()
    refund_detail_ids = fields.One2many(
        comodel_name='l10n.es.aeat.mod349.partner_refund_detail',
        inverse_name='refund_id', string='Partner refund detail IDS',
    )

    @api.multi
    @api.depends('partner_vat', 'country_id', 'total_operation_amount',
                 'total_origin_amount')
    def _compute_partner_refund_ok(self):
        """Checks if partner refund line have all fields filled."""
        for record in self:
            record.partner_refund_ok = bool(
                record.partner_vat and record.country_id and
                record.total_operation_amount >= 0.0 and
                record.total_origin_amount >= 0.0
            )

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
