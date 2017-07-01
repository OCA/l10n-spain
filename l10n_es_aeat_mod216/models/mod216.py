# -*- coding: utf-8 -*-
# Copyright 2015 AvanzOSC - Ainara Galdona
# Copyright 2015 Pedro M. Baeza
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class L10nEsAeatMod216Report(models.Model):

    _description = 'AEAT 216 report'
    _inherit = 'l10n.es.aeat.report.tax.mapping'
    _name = 'l10n.es.aeat.mod216.report'
    _aeat_number = '216'

    casilla_01 = fields.Integer(
        string="[01] # Recipients", readonly=True,
        compute='_compute_casilla_01',
        help="Income subject to retention - Number of recipients")
    casilla_03 = fields.Float(
        string="[03] Amount of retentions",
        readonly=True, compute='_compute_casilla_03',
        help="Income subject to retention - Amount of retentions")
    casilla_04 = fields.Integer(
        string="[04] # Recipients", readonly=True,
        states={'calculated': [('readonly', False)]},
        help="Income not subject to retention - Number of recipients")
    casilla_05 = fields.Float(
        string="[05] Base amount", readonly=True,
        states={'calculated': [('readonly', False)]},
        help="Income not subject to retention - Base amount")
    casilla_06 = fields.Float(
        string="[06] Fees to compensate", readonly=True,
        states={'calculated': [('readonly', False)]},
        help="Fee to compensate for prior results with same subject, "
             "fiscal year and period (in which his statement was to return "
             "and compensation back option was chosen).")
    casilla_07 = fields.Integer(
        string="[07] Result", readonly=True,
        compute='_compute_casilla_07',
        help="Result: ([03] - [06])")
    tipo_declaracion = fields.Selection(
        selection=[
            ('I', "To enter"),
            ('U', "Direct debit"),
            ('G', "To enter on CCT"),
            ('N', "To return")
        ], string="Result type", readonly=True, default='I',
        states={'draft': [('readonly', False)]}, required=True)

    @api.multi
    def _get_partner_domain(self):
        res = super(L10nEsAeatMod216Report, self)._get_partner_domain()
        partners = self.env['res.partner'].search(
            [('is_non_resident', '=', True)])
        res += [('partner_id', 'in', partners.ids)]
        return res

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
    @api.depends('tax_line_ids', 'tax_line_ids.amount')
    def _compute_casilla_03(self):
        for report in self:
            tax_lines = report.tax_line_ids.filtered(
                lambda x: x.field_number == 3)
            report.casilla_03 = sum(tax_lines.mapped('amount'))

    @api.multi
    @api.depends('casilla_03', 'casilla_06')
    def _compute_casilla_07(self):
        for report in self:
            report.casilla_07 = report.casilla_03 - report.casilla_06
