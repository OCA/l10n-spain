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
from odoo import models, fields, api, exceptions, _


def _format_partner_vat(partner_vat=None, country=None):
    """Formats VAT to match XXVATNUMBER (where XX is country code)."""
    if country.code:
        country_pattern = "%s|%s.*" % (country.code, country.code.lower())
        vat_regex = re.compile(country_pattern, re.UNICODE | re.X)
        if partner_vat and not vat_regex.match(partner_vat):
            partner_vat = country.code + partner_vat
    return partner_vat


class Mod349(models.Model):
    _inherit = "l10n.es.aeat.report"
    _name = "l10n.es.aeat.mod349.report"
    _description = "AEAT Model 349 Report"
    _period_monthly = True
    _period_quarterly = True
    _period_yearly = True
    _aeat_number = '349'

    frequency_change = fields.Boolean(
        string='Frequency change', states={'confirmed': [('readonly', True)]})
    total_partner_records = fields.Integer(
        compute="_compute_report_regular_totals", string="Partners records",
        store=True,
    )
    total_partner_records_amount = fields.Float(
        compute="_compute_report_regular_totals",
        string="Partners records amount",
        store=True,
    )
    total_partner_refunds = fields.Integer(
        compute="_compute_report_refund_totals", string="Partners refunds",
        store=True,
    )
    total_partner_refunds_amount = fields.Float(
        compute="_compute_report_refund_totals",
        string="Partners refunds amount",
        store=True,
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

    def _create_349_details(self, move_lines):
        for move_line in move_lines:
            if move_line.invoice_id.type in ('in_refund', 'out_refund'):
                # Check for refunds if the origin invoice period is different
                # from the declaration
                origin_invoice = move_line.invoice_id.refund_invoice_id
                if origin_invoice:
                    if (origin_invoice.date < self.date_start or
                            origin_invoice.date > self.date_end):
                        self._create_349_refund_detail(move_line)
                        continue
            self._create_349_record_detail(move_line)

    def _create_349_record_detail(self, move_line):
        types = move_line.move_id.mapped('line_ids.account_id.internal_type')
        sign = 1 if 'payable' in types else -1
        return self.env['l10n.es.aeat.mod349.partner_record_detail'].create({
            'report_id': self.id,
            'move_line_id': move_line.id,
            'amount_untaxed': sign * move_line.balance,
        })

    def _create_349_refund_detail(self, move_line):
        types = move_line.move_id.mapped('line_ids.account_id.internal_type')
        sign = 1 if 'receivable' in types else -1
        return self.env['l10n.es.aeat.mod349.partner_refund_detail'].create({
            'report_id': self.id,
            'refund_line_id': move_line.id,
            'amount_untaxed': sign * move_line.balance,
        })

    def _create_349_invoice_records(self):
        """creates partner records in 349"""
        rec_obj = self.env['l10n.es.aeat.mod349.partner_record']
        detail_obj = self.env['l10n.es.aeat.mod349.partner_record_detail']
        data = {}
        for record_detail in self.partner_record_detail_ids:
            move_line = record_detail.move_line_id
            partner = move_line.partner_id
            op_key = move_line.l10n_es_aeat_349_operation_key
            partner_dict = data.setdefault(partner, {})
            op_key_dict = partner_dict.setdefault(
                op_key, {'record_details': detail_obj},
            )
            op_key_dict['record_details'] += record_detail
        for partner in list(data.keys()):
            for op_key in list(data[partner].keys()):
                record_created = rec_obj.create({
                    'report_id': self.id,
                    'partner_id': partner.id,
                    'partner_vat': _format_partner_vat(
                        partner_vat=partner.vat,
                        country=partner.country_id,
                    ),
                    'operation_key': op_key,
                    'country_id': partner.country_id.id,
                })
                for record_detail in data[partner][op_key]['record_details']:
                    record_detail.partner_record_id = record_created
        return True

    def _create_349_refund_records(self):
        """Creates restitution records in 349"""
        self.ensure_one()
        detail_obj = self.env['l10n.es.aeat.mod349.partner_record_detail']
        obj = self.env['l10n.es.aeat.mod349.partner_refund']
        refund_detail_obj = self.env[
            'l10n.es.aeat.mod349.partner_refund_detail'
        ]
        move_line_obj = self.env['account.move.line']
        taxes = self._get_taxes()
        data = {}
        # This is for avoiding to find same lines several times
        visited_details = self.env['l10n.es.aeat.mod349.partner_record_detail']
        visited_move_lines = self.env['account.move.line']
        for refund_detail in self.partner_refund_detail_ids:
            move_line = refund_detail.refund_line_id
            partner = move_line.partner_id
            op_key = move_line.l10n_es_aeat_349_operation_key
            origin_invoice = move_line.invoice_id.refund_invoice_id
            if not origin_invoice:
                # TODO: Instead continuing, generate an empty record and a msg
                continue
            # Fetch the latest presentation made for this move
            original_detail = detail_obj.search([
                ('move_line_id.invoice_id', '=', origin_invoice.id),
                ('partner_record_id.operation_key', '=', op_key),
                ('id', 'not in', visited_details.ids)
            ], limit=1, order='report_id desc')
            if original_detail:
                # There's a previous 349 declaration report
                origin_amount = original_detail.amount_untaxed
                period_type = original_detail.report_id.period_type
                year = original_detail.report_id.year
                visited_details |= original_detail
            else:
                # There's no previous 349 declaration report in Odoo
                original_amls = move_line_obj.search([
                    ('tax_ids', 'in', taxes.ids),
                    ('l10n_es_aeat_349_operation_key', '=', op_key),
                    ('invoice_id', '=', origin_invoice.id),
                ])
                origin_amount = abs(sum(
                    (original_amls - visited_move_lines).mapped('balance')
                ))
                visited_move_lines |= original_amls
                # We have to guess the period type, as we don't have that info
                # through move lines. Inferred from:
                # * current record period scheme (monthly/quarterly/yearly)
                # * date of the move line
                if original_amls:
                    original_move = original_amls[:1]
                    year = original_move.date[:4]
                    month = original_move.date[5:7]
                else:
                    continue  # We can't find information to attach to
                if self.period_type == '0A':
                    period_type = '0A'
                elif self.period_type in ('1T', '2T', '3T', '4T'):
                    period_type = '%sT' % int(month) % 4
                else:
                    period_type = month
            key = (partner, op_key, period_type, year)
            key_vals = data.setdefault(key, {
                'original_amount': 0,
                'refund_details': refund_detail_obj,
            })
            key_vals['original_amount'] += origin_amount
            key_vals['refund_details'] += refund_detail
        for key, key_vals in data.items():
            partner, op_key, period_type, year = key
            partner_refund = obj.create({
                'report_id': self.id,
                'partner_id': partner.id,
                'partner_vat': _format_partner_vat(
                    partner_vat=partner.vat,
                    country=partner.country_id,
                ),
                'operation_key': op_key,
                'country_id': partner.country_id.id,
                'total_origin_amount': key_vals['original_amount'],
                'period_type': period_type,
                'year': year,
            })
            key_vals['refund_details'].write({
                'refund_id': partner_refund.id,
            })

    def _account_move_line_domain(self, taxes):
        """Return domain for searching move lines.

        :param: taxes: Taxes to look for in move lines.
        """
        return [('date', '>=', self.date_start),
                ('date', '<=', self.date_end),
                ('tax_ids', 'in', taxes.ids)]

    @api.model
    def _get_taxes(self):
        tax_obj = self.env['account.tax']
        # Obtain all the taxes to be considered
        map_lines = self.env['aeat.349.map.line'].search([])
        tax_templates = map_lines.mapped('tax_tmpl_ids').mapped('description')
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
        self.ensure_one()
        with self.env.norecompute():
            # Remove previous partner records and partner refunds in report
            self.partner_record_ids.unlink()
            self.partner_refund_ids.unlink()
            self.partner_record_detail_ids.unlink()
            self.partner_refund_detail_ids.unlink()
            taxes = self._get_taxes()
            # Get all the account moves
            move_lines = self.env['account.move.line'].search(
                self._account_move_line_domain(taxes)
            )
            # If the type of presentation is complementary, remove records that
            # already exist in other presentations
            if self.type == 'C':
                prev_details = self.partner_record_detail_ids.search([
                    ('move_line_id', 'in', move_lines.ids),
                    ('report_id', '!=', self.id),
                ])
                move_lines -= prev_details.mapped('move_line_id')
                prev_details = self.partner_refund_detail_ids.search([
                    ('refund_line_id', 'in', move_lines.ids),
                    ('report_id', '!=', self.id),
                ])
                move_lines -= prev_details.mapped('refund_line_id')
            self._create_349_details(move_lines)
            self._create_349_invoice_records()
            self._create_349_refund_records()
        # Recompute all pending computed fields
        self.recompute()
        return True

    @api.multi
    def _check_report_lines(self):
        """Checks if all the fields of all the report lines
        (partner records and partner refund) are filled
        """
        for item in self:
            for partner_record in item.partner_record_ids:
                if not partner_record.partner_record_ok:
                    raise exceptions.Warning(
                        _("All partner records fields (country, VAT number) "
                          "must be filled."))
            for partner_record in item.partner_refund_ids:
                if not partner_record.partner_refund_ok:
                    raise exceptions.Warning(
                        _("All partner refunds fields (country, VAT number) "
                          "must be filled."))

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

    def _selection_operation_key(self):
        return self.env['account.move.line'].fields_get(
            allfields=['l10n_es_aeat_349_operation_key'],
        )['l10n_es_aeat_349_operation_key']['selection']

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
        selection=_selection_operation_key,
        string='Operation key',
    )
    total_operation_amount = fields.Float(
        compute='_compute_total_operation_amount',
        string='Total operation amount',
        store=True,
    )
    partner_record_ok = fields.Boolean(
        compute="_compute_partner_record_ok", string='Partner Record OK',
        help='Checked if partner record is OK',
    )
    record_detail_ids = fields.One2many(
        comodel_name='l10n.es.aeat.mod349.partner_record_detail',
        inverse_name='partner_record_id', string='Partner record detail IDS',
    )

    @api.depends('record_detail_ids')
    def _compute_total_operation_amount(self):
        for record in self:
            record.total_operation_amount = sum(
                record.mapped('record_detail_ids.amount_untaxed')
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
        string='Partner record', ondelete='set null', index=True)
    move_line_id = fields.Many2one(
        comodel_name='account.move.line', string='Journal Item',
        required=True)
    invoice_id = fields.Many2one(
        comodel_name='account.invoice', string='Invoice',
        related='move_line_id.invoice_id',
        readonly=True,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Partner',
        related='partner_record_id.partner_id',
        readonly=True,
    )
    amount_untaxed = fields.Float(string='Amount untaxed')
    date = fields.Date(
        related='move_line_id.invoice_id.date_invoice',
        string="Date",
        readonly=True,
    )


class Mod349PartnerRefund(models.Model):
    _name = 'l10n.es.aeat.mod349.partner_refund'
    _description = 'AEAT 349 Model - Partner refund'
    _order = 'operation_key asc'

    def get_period_type_selection(self):
        report_obj = self.env['l10n.es.aeat.mod349.report']
        return report_obj.get_period_type_selection()

    def _selection_operation_key(self):
        return self.env['account.move.line'].fields_get(
            allfields=['l10n_es_aeat_349_operation_key'],
        )['l10n_es_aeat_349_operation_key']['selection']

    report_id = fields.Many2one(
        comodel_name='l10n.es.aeat.mod349.report', string='AEAT 349 Report ID',
        ondelete="cascade")
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=True,
        index=True,
    )
    partner_vat = fields.Char(string='VAT', size=15)
    operation_key = fields.Selection(
        selection=_selection_operation_key,
        string='Operation key',
    )
    country_id = fields.Many2one(comodel_name='res.country', string='Country')
    total_operation_amount = fields.Float(
        compute='_compute_total_operation_amount',
        string='Total rectified amount',
        store=True,
    )
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

    @api.depends('refund_detail_ids')
    def _compute_total_operation_amount(self):
        for record in self:
            rectified_amount = sum(
                record.mapped('refund_detail_ids.amount_untaxed')
            )
            record.total_operation_amount = (
                record.total_origin_amount - rectified_amount
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
        related='refund_id.partner_id',
        readonly=True,
    )
    refund_line_id = fields.Many2one(
        comodel_name='account.move.line', string='Journal Item',
        required=True)
    invoice_id = fields.Many2one(
        comodel_name='account.invoice', string='Invoice',
        related='refund_line_id.invoice_id',
        readonly=True,
    )
    amount_untaxed = fields.Float(string='Amount untaxed')
    date = fields.Date(
        related='refund_line_id.date',
        string="Date",
        readonly=True,
    )
