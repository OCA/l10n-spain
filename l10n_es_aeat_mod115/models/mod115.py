# Copyright 2015 AvanzOSC - Ainara Galdona
# Copyright 2015 Pedro M. Baeza
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import _, api, fields, models
from openerp.exceptions import UserError


class L10nEsAeatMod115Report(models.Model):

    _description = 'AEAT 115 report'
    _inherit = 'l10n.es.aeat.report.tax.mapping'
    _name = 'l10n.es.aeat.mod115.report'
    _aeat_number = '115'

    casilla_01 = fields.Integer(
        string="[01] # Recipients", readonly=True,
        compute='_compute_casilla_01',
        help="Number of recipients")
    casilla_03 = fields.Float(
        string="[03] Amount of retentions",
        readonly=True, compute='_compute_casilla_03',
        help="Amount of retentions")
    casilla_04 = fields.Float(
        string="[04] Fees to compensate", readonly=True,
        states={'calculated': [('readonly', False)]},
        help="Fee to compensate for prior results with same subject, "
             "fiscal year and period (in which his statement was to return "
             "and compensation back option was chosen).")
    casilla_05 = fields.Float(
        string="[05] Result", readonly=True, compute='_compute_casilla_05',
        help="Result: ([03] - [04])")
    tipo_declaracion = fields.Selection(
        selection=[
            ('I', "To enter"),
            ('U', "Direct debit"),
            ('G', "To enter on CCT"),
            ('N', "To return"),
        ], string="Result type", default='I',
        states={'draft': [('readonly', False)]}, required=True)

    @api.multi
    @api.depends('tax_line_ids', 'tax_line_ids.move_line_ids')
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
        """Check bank account completion."""
        msg = ""
        for report in self.filtered(lambda x: not x.partner_bank_id):
            if report.tipo_declaracion in ('U', 'N'):
                msg = (
                    _('Select an account for making the charge') if
                    report.tipo_declaracion == 'U' else
                    _('Select an account for receiving the money')
                )
        if msg:
            raise UserError(msg)
        return super(L10nEsAeatMod115Report, self).button_confirm()

    @api.multi
    def calculate(self):
        super(L10nEsAeatMod115Report, self).calculate()
        for rec in self:
            if rec.casilla_05 < 0.0:
                rec.tipo_declaracion = 'N'
            else:
                rec.tipo_declaracion = 'I'
