# -*- coding: utf-8 -*-
# Copyright 2015 AvanzOSC - Ainara Galdona
# Copyright 2015 Pedro M. Baeza
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, api, _
from odoo.exceptions import Warning as UserError


class L10nEsAeatMod115Report(models.Model):

    _description = 'AEAT 115 report'
    _inherit = 'l10n.es.aeat.report.tax.mapping'
    _name = 'l10n.es.aeat.mod115.report'
    _aeat_number = '115'

    def _get_export_conf(self):
        try:
            return self.env.ref(
                'l10n_es_aeat_mod115.aeat_mod115_2017_main_export_config').id
        except ValueError:
            return self.env['aeat.model.export.config']

    export_config = fields.Many2one(default=_get_export_conf)
    casilla_01 = fields.Integer(
        string="[01] # Recipients", readonly=True, compute_sudo=True,
        compute='_compute_casilla_01',
        help="Number of recipients")
    casilla_03 = fields.Float(
        string="[03] Amount of retentions",
        readonly=True, compute='_compute_casilla_03', compute_sudo=True,
        help="Amount of retentions")
    casilla_04 = fields.Float(
        string="[04] Fees to compensate", readonly=True,
        states={'calculated': [('readonly', False)]},
        help="Fee to compensate for prior results with same subject, "
             "fiscal year and period (in which his statement was to return "
             "and compensation back option was chosen).")
    casilla_05 = fields.Float(
        string="[05] Result", readonly=True, compute='_compute_casilla_05',
        compute_sudo=True, help="Result: ([03] - [04])")
    tipo_declaracion = fields.Selection(
        selection=[
            ('I', "To enter"),
            ('U', "Direct debit"),
            ('G', "To enter on CCT"),
            ('N', "To return")
        ], string="Result type", readonly=True, default='I',
        states={'draft': [('readonly', False)]}, required=True)

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
    @api.depends('casilla_03', 'casilla_04')
    def _compute_casilla_05(self):
        for report in self:
            report.casilla_05 = report.casilla_03 - report.casilla_04

    @api.multi
    def button_confirm(self):
        """Check records"""
        msg = ""
        for report in self:
            if report.tipo_declaracion == 'U' and not report.bank_account_id:
                msg = _('Select an account for making the charge')
            if report.tipo_declaracion == 'N' and not report.bank_account_id:
                msg = _('Select an account for receiving the money')
        if msg:
            raise UserError(msg)
        return super(L10nEsAeatMod115Report, self).button_confirm()
