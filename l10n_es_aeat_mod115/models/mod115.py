# -*- encoding: utf-8 -*-
##############################################################################
#
#  OpenERP, Open Source Management Solution.
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import fields, models, api, _


class L10nEsAeatMod115Report(models.Model):

    _description = 'AEAT 115 report'
    _inherit = 'l10n.es.aeat.report.tax.mapping'
    _name = 'l10n.es.aeat.mod115.report'

    number = fields.Char(default='115')
    casilla_01 = fields.Integer(
        string='[01] Número de perceptores', readonly=True,
        states={'calculated': [('readonly', False)]},
        help="Casilla [01] Liquidación - Retenciones e ingresos a cuenta - "
             "Número de perceptores")
    casilla_02 = fields.Float(
        string='[02] Base retenciones', readonly=True,
        states={'calculated': [('readonly', False)]},
        help="Casilla [02] Liquidación - Retenciones e ingresos a cuenta - "
             "Base de las retenciones e ingresos a cuenta")
    casilla_03 = fields.Float(
        string='[03] Retenciones', readonly=True,
        states={'calculated': [('readonly', False)]},
        help="Casilla [03] Liquidación - Retenciones e ingresos a cuenta - "
             "Retenciones e ingresos a cuenta")
    casilla_04 = fields.Float(
        string='[04] Resultados a ingresar anteriores', readonly=True,
        states={'calculated': [('readonly', False)]},
        help="Casilla [04] Liquidación - Retenciones e ingresos a cuenta - "
             "A deducir (exclusivamente en caso de declaración "
             "complementaria) Resultado a ingresar de la anterior o "
             "anteriores declaraciones del mismo concepto, ejercicio y "
             "período")
    casilla_05 = fields.Float(
        string='[05] Resultado a ingresar', readonly=True,
        compute='get_casilla05',
        help='Casilla [04] Liquidación - Retenciones e ingresos a cuenta - '
             'Resultado a ingresar: ([03] - [04])')
    move_lines_02 = fields.Many2many(
        comodel_name='account.move.line',
        relation='mod115_account_move_line02_rel',
        column1='mod115', column2='account_move_line')
    move_lines_03 = fields.Many2many(
        comodel_name='account.move.line',
        relation='mod115_account_move_line03_rel',
        column1='mod115', column2='account_move_line')
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

    @api.one
    @api.depends('casilla_03', 'casilla_04')
    def get_casilla05(self):
        self.casilla_05 = self.casilla_03 - self.casilla_04

    def __init__(self, pool, cr):
        self._aeat_number = '115'
        super(L10nEsAeatMod115Report, self).__init__(pool, cr)

    @api.multi
    def calculate(self):
        self.ensure_one()
        move_lines02 = self._get_tax_code_lines(['RBI'], periods=self.periods)
        move_lines03 = self._get_tax_code_lines(
            ['RLC115'], periods=self.periods)
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
        view_id = self.env.ref('l10n_es_aeat.view_move_line_tree')
        return {'type': 'ir.actions.act_window',
                'name': _('Account Move Lines'),
                'view_mode': 'tree,form',
                'view_type': 'form',
                'views': [(view_id.id, 'tree')],
                'view_id': False,
                'res_model': 'account.move.line',
                'domain': [('id', 'in', move_lines)]
                }
