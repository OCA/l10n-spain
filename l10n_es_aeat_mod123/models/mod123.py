# -*- coding: utf-8 -*-
# 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models, api, _


class L10nEsAeatMod123Report(models.Model):
    _description = 'AEAT 123 report'
    _inherit = 'l10n.es.aeat.report.tax.mapping'
    _name = 'l10n.es.aeat.mod123.report'

    number = fields.Char(default='123')
    casilla_01 = fields.Integer(
        string='[01] Número de perceptores', readonly=True,
        states={'calculated': [('readonly', False)]},
        help="Casilla [01] Número de perceptores")
    casilla_02 = fields.Float(
        string='[02] Base retenciones', readonly=True,
        states={'calculated': [('readonly', False)]},
        help="Casilla [02] Base de la retención y/o del ingreso a cuenta")
    move_lines_02 = fields.Many2many(
        comodel_name='account.move.line',
        relation='mod123_account_move_line02_rel',
        column1='mod123', column2='account_move_line')
    casilla_03 = fields.Float(
        string='[03] Retenciones', readonly=True,
        states={'calculated': [('readonly', False)]},
        help="Casilla [03] Retenciones e ingresos a cuenta")
    move_lines_03 = fields.Many2many(
        comodel_name='account.move.line',
        relation='mod123_account_move_line03_rel',
        column1='mod123', column2='account_move_line')
    casilla_04 = fields.Float(
        string='[04] Ingresos ejercicios anteriores', readonly=True,
        states={'calculated': [('readonly', False)]},
        help="Casilla [04] Periodificación - Ingresos ejercicios anteriores")
    casilla_05 = fields.Float(
        string='[05] Regularización', readonly=True,
        states={'calculated': [('readonly', False)]},
        help="Casilla [05] Periodificación - Regularización")
    casilla_06 = fields.Float(
        string='[06] Total retenciones', readonly=True,
        compute='_compute_casilla06',
        help='Casilla [06] Suma de retenciones e ingresos a cuenta y '
             'regularización, en su caso ([3] + [5])')
    casilla_07 = fields.Float(
        string='[07] Ingresos ejercicios anteriores', readonly=True,
        states={'calculated': [('readonly', False)]},
        help="Casilla [07] A deducir (exclusivamente en caso de declaración "
             "complementaria) Resultados a ingresar de anteriores "
             "declaraciones por el mismo concepto, ejercicio y período")
    casilla_08 = fields.Float(
        string='[08] Resultado a ingresar', readonly=True,
        compute='_compute_casilla08')
    currency_id = fields.Many2one(
        comodel_name='res.currency', string='Moneda', readonly=True,
        related='company_id.currency_id', store=True)
    tipo_declaracion = fields.Selection(
        selection=[('I', 'Ingreso'),
                   ('U', 'Domiciliación'),
                   ('G', 'Ingreso a anotar en CCT'),
                   ('N', 'Negativa')],
        string='Tipo de declaración', readonly=True,
        states={'draft': [('readonly', False)]}, required=True)

    @api.depends('casilla_03', 'casilla_05')
    def _compute_casilla06(self):
        for report in self:
            report.casilla_06 = self.casilla_03 + self.casilla_05

    @api.depends('casilla_03', 'casilla_05')
    def _compute_casilla08(self):
        for report in self:
            report.casilla_08 = self.casilla_06 + self.casilla_07

    def __init__(self, pool, cr):
        self._aeat_number = '123'
        super(L10nEsAeatMod123Report, self).__init__(pool, cr)

    @api.multi
    def calculate(self):
        self.ensure_one()
        move_lines02 = self._get_tax_code_lines(
            ['RBI123'], periods=self.periods)
        move_lines03 = self._get_tax_code_lines(
            ['RICC123'], periods=self.periods)
        self.move_lines_02 = move_lines02.ids
        self.move_lines_03 = move_lines03.ids
        self.casilla_02 = sum(move_lines02.mapped('tax_amount'))
        self.casilla_03 = sum(move_lines03.mapped('tax_amount'))
        partners = (move_lines02 + move_lines03).mapped('partner_id')
        self.casilla_01 = len(set(partners.ids))

    @api.multi
    def show_move_lines(self):
        move_lines = []
        if self.env.context.get('move_lines02', False):
            move_lines = self.move_lines_02.ids
        elif self.env.context.get('move_lines03', False):
            move_lines = self.move_lines_03.ids
        return {
            'type': 'ir.actions.act_window',
            'name': _('Account Move Lines'),
            'view_mode': 'tree,form',
            'view_type': 'form',
            'res_model': 'account.move.line',
            'domain': [('id', 'in', move_lines)]
        }
