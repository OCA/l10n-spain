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

from openerp import fields, models, api, exceptions, _


class L10nEsAeatMod115Report(models.Model):

    _description = 'AEAT 115 report'
    _inherit = 'l10n.es.aeat.report'
    _name = 'l10n.es.aeat.mod115.report'

    number = fields.Char(default='115')
    casilla_01 = fields.Integer('Casilla [01]', readonly=True,
                                states={'calculated': [('readonly', False)]},
                                help='Retenciones e ingresos a cuenta. '
                                'Número perceptores.')
    casilla_02 = fields.Float('Casilla [02]', readonly=True,
                              states={'calculated': [('readonly', False)]},
                              help='Retenciones e ingresos a cuenta. '
                              'Base retenciones e ingresos a cuenta.')
    casilla_03 = fields.Float('Casilla [03]', readonly=True,
                              states={'calculated': [('readonly', False)]},
                              help='Retenciones e ingresos a cuenta. '
                              'Retenciones e ingresos a cuenta.')
    casilla_04 = fields.Integer('Casilla [04]', readonly=True,
                                states={'calculated': [('readonly', False)]},
                                help='Retenciones e ingresos a cuenta. '
                                'Resultado anteriores declaraciones.')
    casilla_05 = fields.Integer('Casilla [05]',
                                help='Retenciones e ingresos a cuenta. '
                                'Resultado a ingresar.',
                                compute='get_casilla05')
    move_lines_02 = fields.Many2many(comodel_name='account.move.line',
                                     relation='mod115_account_move_line02_rel',
                                     column1='mod115',
                                     column2='account_move_line')
    move_lines_03 = fields.Many2many(comodel_name='account.move.line',
                                     relation='mod115_account_move_line03_rel',
                                     column1='mod115',
                                     column2='account_move_line')
    currency_id = fields.Many2one('res.currency', string='Moneda',
                                  related='company_id.currency_id', store=True)
    period_id = fields.Many2one('account.period', 'Periodo', readonly=True,
                                states={'draft': [('readonly', False)]},
                                required=True)
    tipo_declaracion = fields.Selection(
        [('I', 'Ingreso'), ('U', 'Domiciliación'),
         ('G', 'Ingreso a anotar en CCT'), ('N', 'Negativa')],
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
    def _calc_prev_trimesters_data(self):
        self.ensure_one()
        periods = self.env['account.period'].search(
            [('fiscalyear_id', '=', self.fiscalyear_id.id),
             ('special', '=', False)])
        amount = 0
        for period in periods:
            if period == self.period_id:
                break
            report_ids = self.search(
                [('period_id', '=', period.id),
                 ('fiscalyear_id', '=', self.fiscalyear_id.id),
                 ('company_id', '=', self.company_id.id)])
            if not report_ids:
                raise exceptions.Warning(
                    "No se ha encontrado la declaracion mod. 115 para el "
                    "periodo %s. No se puede continuar el calculo si no "
                    "existe dicha declaracion." % period.code)
            amount = report_ids[0].casilla_05 or 0
        return amount

    @api.multi
    def calculate(self):
        self.ensure_one()
        move_lines02 = self._get_tax_code_lines(
            'RBI', periods=self.period_id)
        move_lines03 = self._get_tax_code_lines(
            'RLC115', periods=self.period_id)
        self.move_lines_02 = move_lines02.ids
        self.move_lines_03 = move_lines03.ids
        self.casilla_02 = sum([x.tax_amount for x in move_lines02])
        self.casilla_03 = sum([x.tax_amount for x in move_lines03])
        self.casilla_04 = self._calc_prev_trimesters_data()
        self.casilla_01 = len(set([x.partner_id for x in (move_lines02 +
                                                          move_lines03)]))

    @api.multi
    def show_move_lines(self):
        move_lines = []
        if self.env.context.get('move_lines02', False):
            move_lines = self.move_lines_02.ids
        elif self.env.context.get('move_lines03', False):
            move_lines = self.move_lines_03.ids
        return {'type': 'ir.actions.act_window',
                'name': _('Account Move Lines'),
                'view_mode': 'tree,form',
                'view_type': 'form',
                'res_model': 'account.move.line',
                'domain': [('id', 'in', move_lines)]
                }
