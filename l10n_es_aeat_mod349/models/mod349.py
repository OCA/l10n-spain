# -*- coding: utf-8 -*-
# Copyright 2004-2011 - Pexego Sistemas Informáticos. (http://pexego.es)
# Copyright 2013 - Top Consultant Software Creations S.L.
#                - (http://www.topconsultant.es/)
# Copyright 2014 - Serv. Tecnol. Avanzados
#                - Pedro M. Baeza (http://www.serviciosbaeza.com)
# Copyright 2016 - Tecnativa - Angel Moya <odoo@tecnativa.com>
# Copyright 2017 - Tecnativa - Luis M. Ontalba <luis.martinez@tecnativa.com>
# Copyright 2017 - Eficent Business and IT Consulting Services, S.L.
#                  <contact@eficent.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

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

    def _get_export_config(self, date):
        res = super(Mod349, self)._get_export_config(date)
        if not res:
            return self.env.ref(
                'l10n_es_aeat_mod349.aeat_mod349_main_export_config')
    frequency_change = fields.Boolean(
        string='Frequency change', states={'confirmed': [('readonly', True)]})
    total_partner_records = fields.Integer(
        compute="_compute_report_regular_totals", string="Partners records",
        readonly=True
    )
    total_partner_records_amount = fields.Float(
        compute="_compute_report_regular_totals",
        string="Partners records amount", readonly=True
    )
    total_partner_refunds = fields.Integer(
        compute="_compute_report_refund_totals", string="Partners refunds",
    )
    total_partner_refunds_amount = fields.Float(
        compute="_compute_report_refund_totals",
        string="Partners refunds amount", readonly=True,
    )
    partner_record_ids = fields.One2many(
        comodel_name='l10n.es.aeat.mod349.partner_record',
        inverse_name='report_id', string='Partner records', ondelete='cascade',
        readonly=True,
    )
    partner_record_detail_ids = fields.One2many(
        comodel_name='l10n.es.aeat.mod349.partner_record_detail',
        inverse_name='report_id', string='Partner record details',
        ondelete='cascade',
        states={'confirmed': [('readonly', True)]},
    )
    partner_refund_ids = fields.One2many(
        comodel_name='l10n.es.aeat.mod349.partner_refund',
        inverse_name='report_id', string='Partner refund IDS',
        ondelete='cascade', readonly=True,
    )
    partner_refund_detail_ids = fields.One2many(
        comodel_name='l10n.es.aeat.mod349.partner_refund_detail',
        inverse_name='report_id', string='Partner refund details',
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

    def _create_349_record_detail(self, move_lines):
        detail_obj = self.env['l10n.es.aeat.mod349.partner_record_detail']
        refund_details = detail_obj
        for move_line in move_lines:
            if move_line.invoice_id.type not in (
                    'in_refund', 'out_refund'):
                balance = abs(move_line.balance)
            else:
                balance = -abs(move_line.balance)
            refund_details += detail_obj.create(
                {'report_id': self.id,
                 'move_line_id': move_line.id,
                 'amount_untaxed': balance})
        return refund_details

    def _create_349_refund_detail(self, move_lines):
        detail_obj = self.env['l10n.es.aeat.mod349.partner_refund_detail']
        record_details = detail_obj
        for move_line in move_lines:
            if move_line.invoice_id.type in (
                    'in_refund', 'out_refund'):
                balance = abs(move_line.balance)
            else:
                balance = -abs(move_line.balance)
            record_details += detail_obj.create(
                {'report_id': self.id,
                 'refund_line_id': move_line.id,
                 'amount_untaxed': balance})
        return record_details

    def _create_349_invoice_records(self):
        """creates partner records in 349"""
        rec_obj = self.env['l10n.es.aeat.mod349.partner_record']
        detail_obj = self.env['l10n.es.aeat.mod349.partner_record_detail']
        data = {}
        for record_detail in self.partner_record_detail_ids:
            move_line = record_detail.move_line_id
            partner = move_line.partner_id
            op_key = move_line.aeat_349_operation_key
            if partner not in data.keys():
                data[partner] = {}
            if op_key not in data[partner].keys():
                data[partner][op_key] = {
                    'total_amount': 0.0,
                    'record_details': detail_obj
                }
            partner_country = partner.country_id
            data[partner][op_key]['total_amount'] += move_line.balance
            data[partner][op_key]['record_details'] += record_detail
        for partner in data.keys():
            for op_key in data[partner].keys():
                record_created = rec_obj.create(
                    {'report_id': self.id,
                     'partner_id': partner.id,
                     'partner_vat': _format_partner_vat(
                         partner_vat=partner.vat,
                         country=partner_country),
                     'operation_key': op_key.id,
                     'country_id': partner_country.id or False,
                     'total_operation_amount': abs(
                         data[partner][op_key]['total_amount'])
                     })
                for record_detail in data[partner][op_key]['record_details']:
                    record_detail.partner_record_id = record_created
        return True

    def _create_349_refund_records(self):
        """Creates restitution records in 349"""
        detail_obj = self.env[
            'l10n.es.aeat.mod349.partner_record_detail']

        obj = self.env['l10n.es.aeat.mod349.partner_refund']
        refund_detail_obj = self.env[
            'l10n.es.aeat.mod349.partner_refund_detail']
        move_line_obj = self.env['account.move.line']
        taxes = self._get_taxes()
        data = {}
        for refund_detail in self.partner_refund_detail_ids:
            move_line = refund_detail.refund_line_id
            partner = move_line.partner_id
            partner_country = partner.country_id
            op_key = move_line.aeat_349_operation_key
            if partner not in data.keys():
                # dict with operation keys
                data[partner] = {}
            if op_key not in data[partner].keys():
                # dict with original invoices
                data[partner][op_key] = {}

            origin_invoices = move_line.invoice_id.mapped('origin_invoice_ids')
            original_partner_record = detail_obj
            if origin_invoices:
                origin_invoice = origin_invoices[0]
                original_details = detail_obj.search(
                    [('move_line_id.invoice_id', 'in', origin_invoice.ids),
                     ('partner_record_id.operation_key', '=', op_key.id)])
                # Fetch the latest presentation made for this move
                original_details = original_details.sorted(
                    key=lambda r: r.report_id.name, reverse=True)
                if original_details:
                    original_partner_record = \
                        original_details[0].partner_record_id
                    origin_amount = \
                        original_partner_record.total_operation_amount
                else:
                    original_moves = move_line_obj.search(
                        [('tax_ids', 'in', taxes.ids),
                         ('aeat_349_operation_key', '=', op_key.id),
                         ('invoice_id', 'in', origin_invoice.ids)])
                    origin_amount = original_moves and original_moves[
                        0].balance or 0.0
                data[partner][op_key][origin_invoice] = {
                    'original_amount': origin_amount,
                    'rectified_amount': 0.0,
                    'refund_details': refund_detail_obj,
                }
            else:
                # TODO: Instead of continue, generate an empty record and a msg
                continue
            data[partner][op_key][origin_invoice][
                'rectified_amount'] += abs(move_line.balance)
            data[partner][op_key][origin_invoice][
                'refund_details'] += refund_detail

        for partner in data.keys():
            for op_key in data[partner].keys():
                original_amount = 0.0
                rectified_amount = 0.0
                refund_details = refund_detail_obj
                for invoice in data[partner][op_key].keys():
                    invoice_data = data[partner][op_key][invoice]
                    original_amount += invoice_data['original_amount']
                    rectified_amount += invoice_data['rectified_amount']
                    refund_details += invoice_data['refund_details']
                obj_created = obj.create({
                    'report_id': self.id,
                    'partner_id': partner.id,
                    'partner_vat': _format_partner_vat(
                        partner_vat=partner.vat, country=partner_country),
                    'operation_key': op_key.id,
                    'country_id': partner_country.id,
                    'total_operation_amount':
                    original_amount - rectified_amount,
                    'total_origin_amount': original_amount,
                    'period_type':
                    original_partner_record and
                    original_partner_record.report_id.period_type or False,
                    'year': original_partner_record and
                    original_partner_record.report_id.year or False,
                })
                for refund_detail in refund_details:
                    refund_detail.refund_id = obj_created
        return True

    def _account_move_line_domain(self, taxes):
        # search move lines that contain these tax codes
        return [('date', '>=', self.date_start),
                ('date', '<=', self.date_end),
                ('tax_ids', 'in', taxes.ids)]

    def _get_account_moves(self, taxes):
        aml_obj = self.env['account.move.line']
        amls = aml_obj.search(self._account_move_line_domain(taxes))
        return amls.mapped('move_id')

    @api.model
    def _compute_partner_records(self):
        self.partner_record_ids.unlink()
        self._create_349_invoice_records()

    @api.model
    def _compute_refund_records(self):
        self.partner_refund_ids.unlink()
        self._create_349_refund_records()

    @api.model
    def _get_taxes(self):
        tax_obj = self.env['account.tax']
        # Obtain all the taxes to be considered
        map_lines = self.env['aeat.349.map.line'].search([])
        tax_templates = map_lines.mapped('taxes').mapped('description')
        if not tax_templates:
            raise exceptions.Warning(_('No Tax Mapping was found'))
        # search the account.tax referred to by the template
        taxes = tax_obj.search(
            [('description', 'in', tax_templates),
             ('company_id', 'child_of', self.company_id.id)])
        return taxes

    @api.multi
    def calculate(self):
        """Computes the records in report."""
        for mod349 in self:
            # Remove previous partner records and partner refunds in report
            mod349.partner_record_ids.unlink()
            mod349.partner_refund_ids.unlink()
            mod349.partner_record_detail_ids.unlink()
            mod349.partner_refund_detail_ids.unlink()

            taxes = mod349._get_taxes()
            # Get all the account moves
            moves = mod349._get_account_moves(taxes)
            # Get all the move lines that have 349 operation keys
            move_lines = moves.mapped('line_ids').filtered(
                lambda x: x.aeat_349_operation_key)
            # If the type of presentation is not 'S', remove records that
            # already exist in other presentations
            if mod349.type != 'S':
                prev_details = self.env[
                    'l10n.es.aeat.mod349.partner_record_detail'].search(
                    [('move_line_id', 'in', move_lines.ids),
                     ('id', '!=', mod349.id)])
                move_lines -= prev_details.mapped('move_line_id')
                prev_details = self.env[
                    'l10n.es.aeat.mod349.partner_refund_detail'].search(
                    [('refund_line_id', 'in', move_lines.ids),
                     ('id', '!=', mod349.id)])
                move_lines -= prev_details.mapped('refund_line_id')
            # Separates normal move lines from restitution
            refund_lines = move_lines.filtered(
                lambda m: m.invoice_id.type in ('in_refund', 'out_refund'))
            move_lines -= refund_lines
            if move_lines:
                mod349._create_349_record_detail(move_lines)
            if refund_lines:
                mod349._create_349_refund_detail(refund_lines)
            mod349._compute_partner_records()
            mod349._compute_refund_records()
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

    report_id = fields.Many2one(
        comodel_name='l10n.es.aeat.mod349.report', required=True,
        string='AEAT 349 Report ID',
        ondelete="cascade")
    report_type = fields.Selection(
        related='report_id.type', readonly=True, store=True,
    )
    partner_record_id = fields.Many2one(
        comodel_name='l10n.es.aeat.mod349.partner_record',
        default=lambda self: self.env.context.get('partner_record_id'),
        string='Partner record', ondelete='set null', select=1)
    move_line_id = fields.Many2one(
        comodel_name='account.move.line', string='Move Line',
        required=True)
    invoice_id = fields.Many2one(
        comodel_name='account.invoice', string='Invoice',
        related='move_line_id.invoice_id')
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Partner',
        related='partner_record_id.partner_id',
    )
    amount_untaxed = fields.Float(string='Amount untaxed')
    date = fields.Date(related='move_line_id.invoice_id.date_invoice',
                       string="Date",
                       readonly=True)

    @api.multi
    def unlink(self):
        reports = [rec.report_id for rec in self]
        res = super(Mod349PartnerRecordDetail, self).unlink()
        for report in reports:
            report._compute_partner_records()
        return res


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

    report_id = fields.Many2one(
        comodel_name='l10n.es.aeat.mod349.report', required=True,
        string='AEAT 349 Report ID',
        ondelete="cascade")
    report_type = fields.Selection(
        related='report_id.type', readonly=True, store=True,
    )
    refund_id = fields.Many2one(
        comodel_name='l10n.es.aeat.mod349.partner_refund',
        string='Partner refund ID', ondelete="set null")
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Partner',
        related='refund_id.partner_id'
    )
    refund_line_id = fields.Many2one(
        comodel_name='account.move.line', string='Move Line ID',
        required=True)
    invoice_id = fields.Many2one(
        comodel_name='account.invoice', string='Invoice',
        related='refund_line_id.invoice_id')
    amount_untaxed = fields.Float(string='Amount untaxed')
    date = fields.Date(related='refund_line_id.invoice_id.date_invoice',
                       string="Date",
                       readonly=True)

    @api.multi
    def unlink(self):
        reports = [rec.report_id for rec in self]
        res = super(Mod349PartnerRefundDetail, self).unlink()
        for report in reports:
            report._compute_refund_records()
        return res
