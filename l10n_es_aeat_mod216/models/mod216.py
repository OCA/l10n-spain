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


class L10nEsAeatMod216Report(models.Model):

    _description = 'AEAT 216 report'
    _inherit = 'l10n.es.aeat.report'
    _name = 'l10n.es.aeat.mod216.report'

    number = fields.Char(default='216')
    casilla_01 = fields.Integer(
        'Casilla [01]', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Liquidación - Partida 1 - Núm. Rentas')
    casilla_02 = fields.Float(
        'Casilla [02]', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Liquidación - Partida 2 - Base ret. ing. cuenta')
    casilla_03 = fields.Float(
        'Casilla [03]', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Liquidación - Partida 3 - Retenciones ingresos a cuenta')
    casilla_04 = fields.Integer(
        'Casilla [04]', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Liquidación - Partida 4 - Núm. Rentas')
    casilla_05 = fields.Float(
        'Casilla [05]', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Liquidación - Partida 5 - Base ret. ing. cuenta.')
    casilla_06 = fields.Float(
        'Casilla [06]', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Liquidación - Partida 6 - Resultado ing. anteriores '
             'declaraciones')
    casilla_07 = fields.Integer(
        'Casilla [07]', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Liquidación - Partida 7 - Resultado ingresar')
    currency_id = fields.Many2one(
        'res.currency', string='Moneda',
        related='company_id.currency_id', store=True)
    period_id = fields.Many2one(
        'account.period', 'Periodo', readonly=True,
        states={'draft': [('readonly', False)]}, required=True)
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
            [('is_resident', '=', True)])
        res += [('partner_id', 'in', partners.ids)]
        return res

    @api.multi
    def calculate(self):
        self.ensure_one()
        move_lines_base = self._get_tax_code_lines(
            ['IRPBI'], periods=self.period_id)
        move_lines_cuota = self._get_tax_code_lines(
            ['ITRPC'], periods=self.period_id)
        partner_lst = set([x.partner_id for x in
                           (move_lines_base + move_lines_cuota)])
        self.casilla_01 = len(partner_lst)
        self.casilla_02 = sum(move_lines_base.mapped('tax_amount'))
        self.casilla_03 = sum(move_lines_cuota.mapped('tax_amount'))
