# -*- coding: utf-8 -*-
# Copyright 2015 Ainara Galdona (http://www.avanzosc.es)
# Copyright 2016 RGB Consulting SL (http://www.rgbconsulting.com)
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2016 Vicent Cubells (http://obertix.net)
# Copyright 2016 Jose Maria Alzaga (http://www.aselcis.com)
# Copyright 2016 Ismael Calvo (http://factorlibre.com)
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

from openerp import fields, models, api, _
from openerp.exceptions import Warning as UserError


class L10nEsAeatMod111Report(models.Model):

    _description = 'AEAT 111 report'
    _inherit = 'l10n.es.aeat.report.tax.mapping'
    _name = 'l10n.es.aeat.mod111.report'
    _aeat_number = '111'

    casilla_01 = fields.Integer(
        string="[01] # Recipients", readonly=True,
        compute='_compute_casilla_01', store=True,
        help="Work income - Monetary - Number of recipients")
    casilla_04 = fields.Integer(
        string="[04] # Recipients", readonly=True,
        compute='_compute_casilla_04', store=True,
        help="Work income - In kind - Number of recipients")
    casilla_07 = fields.Integer(
        string="[07] # Recipients", readonly=True,
        compute='_compute_casilla_07', store=True,
        help="Business income - Monetary - Number of recipients")
    casilla_10 = fields.Integer(
        string="[10] # Recipients", readonly=True,
        states={'calculated': [('readonly', False)]},
        help="Business income - In kind - Number of recipients")
    casilla_11 = fields.Float(
        string="[11] Taxable", readonly=True,
        states={'calculated': [('readonly', False)]},
        help="Business income - In kind - Base taxable value")
    casilla_12 = fields.Float(
        string="[12] Amount retained", readonly=True,
        states={'calculated': [('readonly', False)]},
        help="Business income - In kind - Amount retained")
    casilla_13 = fields.Integer(
        string="[13] # Recipients", readonly=True,
        states={'calculated': [('readonly', False)]},
        help="Awards for participation in games, contests, raffles or "
             "random combinations - Monetary - Number of recipients")
    casilla_14 = fields.Float(
        string="[14] Taxable", readonly=True,
        states={'calculated': [('readonly', False)]},
        help="Awards for participation in games, contests, raffles or "
             "random combinations - Monetary - Base taxable value")
    casilla_15 = fields.Float(
        string="[15] Amount retained", readonly=True,
        states={'calculated': [('readonly', False)]},
        help="Awards for participation in games, contests, raffles or "
             "random combinations - Monetary - Amount retained")
    casilla_16 = fields.Integer(
        string="[16] # Recipients", readonly=True,
        states={'calculated': [('readonly', False)]},
        help="Awards for participation in games, contests, raffles or "
             "random combinations - In kind - Number of recipients")
    casilla_17 = fields.Float(
        string="[17] Taxable", readonly=True,
        states={'calculated': [('readonly', False)]},
        help="Awards for participation in games, contests, raffles or "
             "random combinations - In kind - Base taxable value")
    casilla_18 = fields.Float(
        string="[18] Amount retained", readonly=True,
        states={'calculated': [('readonly', False)]},
        help="Awards for participation in games, contests, raffles or "
             "random combinations - In kind - Amount retained")
    casilla_19 = fields.Integer(
        string="[19] # Recipients", readonly=True,
        states={'calculated': [('readonly', False)]},
        help="Capital gains derived from the forest exploitation of "
             "residents in public forests - Monetary - Number of recipients")
    casilla_20 = fields.Float(
        string="[20] Taxable", readonly=True,
        states={'calculated': [('readonly', False)]},
        help="Capital gains derived from the forest exploitation of "
             "residents in public forests - Monetary - Base taxable value")
    casilla_21 = fields.Float(
        string="[21] Amount retained", readonly=True,
        states={'calculated': [('readonly', False)]},
        help="Capital gains derived from the forest exploitation of "
             "residents in public forests - Monetary - Amount retained")
    casilla_22 = fields.Integer(
        string="[22] # Recipients", readonly=True,
        states={'calculated': [('readonly', False)]},
        help="Capital gains derived from the forest exploitation of "
             "residents in public forests - In kind - Number of recipients")
    casilla_23 = fields.Float(
        string="[23] Taxable", readonly=True,
        states={'calculated': [('readonly', False)]},
        help="Capital gains derived from the forest exploitation of "
             "residents in public forests - In kind - Base taxable value")
    casilla_24 = fields.Float(
        string="[24] Amount retained", readonly=True,
        states={'calculated': [('readonly', False)]},
        help="Capital gains derived from the forest exploitation of "
             "residents in public forests - In kind - Amount retained")
    casilla_25 = fields.Integer(
        string="[25] # Recipients", readonly=True,
        states={'calculated': [('readonly', False)]},
        help="Consideration for the transfer of image rights: income "
             "account provided in Article 92.8 of the Tax Law - "
             "Monetary or in kind - Number of recipients")
    casilla_26 = fields.Float(
        string="[26] Taxable", readonly=True,
        states={'calculated': [('readonly', False)]},
        help="Consideration for the transfer of image rights: income "
             "account provided in Article 92.8 of the Tax Law - "
             "Monetary or in kind - Base taxable value")
    casilla_27 = fields.Float(
        string="[27] Amount retained", readonly=True,
        states={'calculated': [('readonly', False)]},
        help="Consideration for the transfer of image rights: income "
             "account provided in Article 92.8 of the Tax Law - "
             "Monetary or in kind - Amount retained")
    casilla_28 = fields.Float(
        string="[28] Amount of retentions",
        readonly=True, compute='_compute_casilla_28',
        help="Amount of retentions: "
             "([03] + [06] + [09] + [12] + [15] + [18] + [21] + [24] + [27])")
    casilla_29 = fields.Float(
        string="[29] Fees to compensate", readonly=True,
        states={'calculated': [('readonly', False)]},
        help="Fee to compensate for prior results with same subject, "
             "fiscal year and period (in which his statement was to return "
             "and compensation back option was chosen).")
    casilla_30 = fields.Float(
        string="[30] Result",
        readonly=True, compute='_compute_casilla_30',
        help="Result: ([28] - [29])")
    codigo_electronico_anterior = fields.Char(
        string='Last electronic code', size=16, readonly=True,
        states={'draft': [('readonly', False)]},
        help="Electronic code of prior statement (if online). To be completed "
             "only in the case of supplementary statement.")
    tipo_declaracion = fields.Selection(
        selection=[
            ('I', "To enter"),
            ('U', "Direct debit"),
            ('G', "To enter on CCT"),
            ('N', "To return")
        ], string="Result type", readonly=True, default='I',
        states={'draft': [('readonly', False)]}, required=True)
    colegio_concertado = fields.Boolean(
        string="College concerted", readonly=True,
        states={'draft': [('readonly', False)]}, default=False)

    @api.multi
    @api.constrains('codigo_electronico_anterior', 'previous_number')
    def _check_complementary(self):
        for report in self:
            if (report.type == 'C' and
                    not report.codigo_electronico_anterior and
                    not report.previous_number):
                raise UserError(
                    _("If supplementary statement box is marked, you must "
                      "complete the electronic code or number of receipt of "
                      "the prior statement."))

    @api.multi
    @api.depends('tax_line_ids', 'tax_line_ids.move_line_ids.partner_id')
    def _compute_casilla_01(self):
        casillas = (2, 3)
        for report in self:
            tax_lines = report.tax_line_ids.filtered(
                lambda x: x.field_number in casillas)
            report.casilla_01 = len(
                tax_lines.mapped('move_line_ids').mapped('partner_id'))

    @api.multi
    @api.depends('tax_line_ids', 'tax_line_ids.move_line_ids.partner_id')
    def _compute_casilla_04(self):
        casillas = (5, 6)
        for report in self:
            tax_lines = report.tax_line_ids.filtered(
                lambda x: x.field_number in casillas)
            report.casilla_04 = len(
                tax_lines.mapped('move_line_ids').mapped('partner_id'))

    @api.multi
    @api.depends('tax_line_ids', 'tax_line_ids.move_line_ids.partner_id')
    def _compute_casilla_07(self):
        casillas = (8, 9)
        for report in self:
            tax_lines = report.tax_line_ids.filtered(
                lambda x: x.field_number in casillas)
            report.casilla_07 = len(
                tax_lines.mapped('move_line_ids').mapped('partner_id'))

    @api.multi
    @api.depends('tax_line_ids', 'tax_line_ids.amount',
                 'casilla_12', 'casilla_15', 'casilla_18',
                 'casilla_21', 'casilla_24', 'casilla_27')
    def _compute_casilla_28(self):
        casillas = (3, 6, 9)
        for report in self:
            tax_lines = report.tax_line_ids.filtered(
                lambda x: x.field_number in casillas)
            report.casilla_28 = (
                sum(tax_lines.mapped('amount')) +
                report.casilla_12 + report.casilla_15 + report.casilla_18 +
                report.casilla_21 + report.casilla_24 + report.casilla_27
            )

    @api.multi
    @api.depends('casilla_28', 'casilla_29')
    def _compute_casilla_30(self):
        for report in self:
            report.casilla_30 = report.casilla_28 - report.casilla_29

    @api.multi
    def button_confirm(self):
        """Check records"""
        msg = ""
        for report in self:
            if report.tipo_declaracion == 'D' and not report.bank_account_id:
                msg = _('Select an account for making the charge')
            if report.tipo_declaracion == 'N' and not report.bank_account_id:
                msg = _('Select an account for receiving the money')
        if msg:
            raise UserError(msg)
        return super(L10nEsAeatMod111Report, self).button_confirm()
