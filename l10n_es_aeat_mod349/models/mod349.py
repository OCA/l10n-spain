# -*- coding: utf-8 -*-
# Copyright 2004-2011 - Pexego Sistemas Informáticos. (http://pexego.es)
# Copyright 2013 - Top Consultant Software Creations S.L.
#                - (http://www.topconsultant.es/)
# Copyright 2014 - Serv. Tecnol. Avanzados
#                - Pedro M. Baeza (http://www.serviciosbaeza.com)
# Copyright 2016 - Tecnativa - Angel Moya <odoo@tecnativa.com>
# Copyright 2017 - Tecnativa - Luis M. Ontalba <luis.martinez@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re
from openerp import models, fields, api, exceptions, _


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

    def _create_349_partner_records(self, move_lines, partner,
                                    operation_key):
        """creates partner records in 349"""
        rec_obj = self.env['l10n.es.aeat.mod349.partner_record']
        partner_country = partner.country_id
        sum_credit = sum([move_line.credit for move_line in
                          move_lines])
        sum_debit = sum([move_line.debit for move_line in
                         move_lines])
        record_created = rec_obj.create(
            {'report_id': self.id,
             'partner_id': partner.id,
             'partner_vat': _format_partner_vat(partner_vat=partner.vat,
                                                country=partner_country),
             'operation_key': operation_key.id,
             'country_id': partner_country.id or False,
             'total_operation_amount': abs(sum_credit - sum_debit)
             })
        for move_line in move_lines:
            if move_line.invoice_id.type not in ('in_refund', 'out_refund'):
                balance = abs(move_line.balance)
            else:
                balance = -abs(move_line.balance)
            detail_obj = self.env['l10n.es.aeat.mod349.partner_record_detail']
            detail_obj.create({'partner_record_id': record_created.id,
                               'move_line_id': move_line.id,
                               'amount_untaxed': balance})
        return record_created

    def _create_349_refund_records(self, refund_lines, partner, operation_key):
        """Creates restitution records in 349"""
        partner_detail_obj = self.env[
            'l10n.es.aeat.mod349.partner_record_detail']
        obj = self.env['l10n.es.aeat.mod349.partner_refund']
        obj_detail = self.env['l10n.es.aeat.mod349.partner_refund_detail']
        partner_country = partner.country_id
        origin_invoices = refund_lines.mapped('invoice_id.origin_invoice_ids')
        refund_details = partner_detail_obj.search(
            [('move_line_id.invoice_id', 'in', origin_invoices.ids),
             ('partner_record_id.operation_key', '=', operation_key.id)])
        if refund_details:
            partner_record = refund_details[0].partner_record_id
            obj_created = obj.create({
                'report_id': self.id,
                'partner_id': partner.id,
                'partner_vat': _format_partner_vat(
                    partner_vat=partner.vat, country=partner_country),
                'operation_key': operation_key.id,
                'country_id': partner_country.id,
                'total_operation_amount': (
                    partner_record.total_operation_amount - sum(
                        [abs(x.balance) for x in refund_lines])),
                'total_origin_amount': partner_record.total_operation_amount,
                'period_type': partner_record.report_id.period_type,
                'year': partner_record.report_id.year})
            for refund_line in refund_lines:
                obj_detail.create({
                     'refund_id': obj_created.id,
                     'refund_line_id': refund_line.id,
                     'amount_untaxed': -refund_line.balance})
        return True

    @api.multi
    def calculate(self):
        """Computes the records in report."""
        partner_obj = self.env['res.partner']
        move_line_obj = self.env['account.move.line']
        op_keys = self.env['aeat.349.map.line'].search([])
        for mod349 in self:
            # Remove previous partner records and partner refunds in report
            mod349.partner_record_ids.unlink()
            mod349.partner_refund_ids.unlink()
            # Returns all commercial partners
            partners = partner_obj.with_context(active_test=False).search(
                [('parent_id', '=', False)])
            for partner in partners:
                for op_key in op_keys:
                    # Move lines
                    move_lines_total = (
                        move_line_obj._get_move_lines_by_type(
                            partner, op_key,
                            mod349.date_start,
                            mod349.date_end))
                    # Separates normal move lines from restitution
                    move_lines, refund_lines = (
                        move_lines_total.clean_refund_move_lines(
                            partner,
                            mod349.date_start,
                            mod349.date_end,))
                    if move_lines:
                        mod349._create_349_partner_records(move_lines,
                                                           partner,
                                                           op_key)
                    if refund_lines:
                        mod349._create_349_refund_records(refund_lines,
                                                          partner,
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
    partner_vat = fields.Char(string='VAT', size=15, select=1)
    country_id = fields.Many2one(comodel_name='res.country', string='Country')
    operation_key = fields.Many2one(
        string='AEAT 349 Operation key',
        comodel_name='aeat.349.map.line',
        store='True',
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
        string='Partner record', required=True, ondelete='cascade', select=1)
    move_line_id = fields.Many2one(
        comodel_name='account.move.line', string='Move Line',
        required=True)
    amount_untaxed = fields.Float(string='Amount untaxed')
    date = fields.Date(related='move_line_id.invoice_id.date_invoice',
                       string="Date",
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
        comodel_name='res.partner', string='Partner', required=1, select=1)
    partner_vat = fields.Char(string='VAT', size=15)
    operation_key = fields.Many2one(
        string='AEAT 349 Operation key',
        comodel_name='aeat.349.map.line',
        store='True',
    )
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
    refund_line_id = fields.Many2one(
        comodel_name='account.move.line', string='Move Line ID',
        required=True)
    amount_untaxed = fields.Float(string='Amount untaxed')
    date = fields.Date(related='refund_line_id.invoice_id.date_invoice',
                       string="Date",
                       readonly=True)
