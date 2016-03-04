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


class L10nEsAeatMod216Report(models.Model):

    _description = 'AEAT 216 report'
    _inherit = 'l10n.es.aeat.report.tax.mapping'
    _name = 'l10n.es.aeat.mod216.report'

    number = fields.Char(default='216')
    casilla_01 = fields.Integer(
        '[01] Número de rentas', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Liquidación - Rentas sometidas a retención/ingreso a cuenta - '
             'Casilla [01] Número de rentas')
    casilla_02 = fields.Float(
        '[02] Base de retenciones', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Liquidación - Rentas sometidas a retención/ingreso a cuenta - '
             'Casilla [02] Base de retenciones e ingresos a cuenta/Importe '
             'de las rentas')
    casilla_03 = fields.Float(
        '[03] Retenciones', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Liquidación - Rentas sometidas a retención/ingreso a cuenta - '
             'Casilla [03] Retenciones e ingresos a cuenta')
    casilla_04 = fields.Integer(
        '[04] Número de rentas', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Liquidación - Rentas no sometidas a retención/ingreso a cuenta'
             ' - Casilla [04] Número de rentas')
    casilla_05 = fields.Float(
        '[05] Base de retenciones', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Liquidación - Rentas no sometidas a retención/ingreso a cuenta'
             ' - Casilla [05] Base de retenciones e ingresos a cuenta/Importe '
             'de las rentas')
    casilla_06 = fields.Float(
        '[06] Resultados a ingresar anteriores', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Liquidación - Casilla [06] A deducir (exclusivamente en caso '
             'de complementaria): Resultados a ingresar de anteriores '
             'declaraciones por el mismo concepto, ejercicio y período')
    casilla_07 = fields.Integer(
        '[07] Resultado a ingresar', readonly=True, compute='_compute_07',
        help='Liquidación - Casilla [07] Resultado a ingresar ([03] - [06])')
    move_lines_base = fields.Many2many(
        string="Account move lines for bases",
        comodel_name='account.move.line',
        relation='mod216_account_move_lines_base_rel',
        column1='mod216', column2='account_move_line')
    move_lines_cuota = fields.Many2many(
        string="Account move lines for amounts",
        comodel_name='account.move.line',
        relation='mod216_account_move_line_cuota_rel',
        column1='mod216', column2='account_move_line')
    currency_id = fields.Many2one(
        'res.currency', string='Moneda', readonly=True,
        related='company_id.currency_id', store=True)
    tipo_declaracion = fields.Selection(
        [('I', 'Ingreso'), ('U', 'Domiciliación'),
         ('G', 'Ingreso a anotar en CCT'), ('N', 'Negativa')],
        string='Tipo de declaración', readonly=True,
        states={'draft': [('readonly', False)]}, required=True)

    def __init__(self, pool, cr):
        self._aeat_number = '216'
        super(L10nEsAeatMod216Report, self).__init__(pool, cr)

    @api.multi
    def _get_partner_domain(self):
        res = super(L10nEsAeatMod216Report, self)._get_partner_domain()
        partners = self.env['res.partner'].search(
            [('is_non_resident', '=', True)])
        res += [('partner_id', 'in', partners.ids)]
        return res

    @api.multi
    def calculate(self):
        self.ensure_one()
        move_lines_base = self._get_tax_code_lines(
            ['IRPBI'], periods=self.periods)
        move_lines_cuota = self._get_tax_code_lines(
            ['ITRPC'], periods=self.periods)
        self.move_lines_base = move_lines_base.ids
        self.move_lines_cuota = move_lines_cuota.ids
        partner_lst = set([x.partner_id for x in
                           (move_lines_base + move_lines_cuota)])
        # I. Rentas sometidas a retención/ingreso a cuenta
        self.casilla_01 = len(partner_lst)
        self.casilla_02 = sum(move_lines_base.mapped('tax_amount'))
        self.casilla_03 = sum(move_lines_cuota.mapped('tax_amount'))
        # II. Rentas no sometidas a retención/ingreso a cuenta
        #     No existe código de impuesto para calcular las bases
        #     de la rentas no sometidas a retención.
        #     El usuario introduce este dato de manera manual.

    @api.one
    @api.depends('casilla_03', 'casilla_06')
    def _compute_07(self):
        self.casilla_07 = self.casilla_03 - self.casilla_06

    @api.multi
    def show_move_lines(self):
        move_lines = []
        if self.env.context.get('move_lines_base', False):
            move_lines = self.move_lines_base.ids
        elif self.env.context.get('move_lines_cuota', False):
            move_lines = self.move_lines_cuota.ids
        return {'type': 'ir.actions.act_window',
                'name': _('Account Move Lines'),
                'view_mode': 'tree,form',
                'view_type': 'form',
                'res_model': 'account.move.line',
                'domain': [('id', 'in', move_lines)]
                }
