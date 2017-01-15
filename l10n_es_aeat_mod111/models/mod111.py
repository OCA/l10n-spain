# -*- coding: utf-8 -*-
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


class L10nEsAeatMod111Report(models.Model):

    _description = 'AEAT 111 report'
    _inherit = 'l10n.es.aeat.report.tax.mapping'
    _name = 'l10n.es.aeat.mod111.report'

    def _get_export_conf(self):
        try:
            return self.env.ref(
                'l10n_es_aeat_mod111.aeat_mod111_main_export_config').id
        except ValueError:
            return self.env['aeat.model.export.config']

    number = fields.Char(default='111')
    export_config = fields.Many2one(default=_get_export_conf)
    casilla_01 = fields.Integer(
        string='[01] Nº de perceptores', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Casilla [01]: Rendimientos del trabajo - '
             'Rendimientos dinerarios - Nº de perceptores')
    casilla_02 = fields.Float(
        string='[02] Importe de las percepciones', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Casilla [02]: Rendimientos del trabajo - '
             'Rendimientos dinerarios - Importe de las percepciones')
    casilla_03 = fields.Float(
        string='[03] Importe de las retenciones', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Casilla [03]: Rendimientos del trabajo - '
             'Rendimientos dinerarios - Importe de las retenciones')
    casilla_04 = fields.Integer(
        string='[04] Nº de perceptores', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Casilla [04]: Rendimientos del trabajo - '
             'Rendimientos en especie - Nº de perceptores')
    casilla_05 = fields.Float(
        string='[05] Valor percepciones en especie', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Casilla [05]: Rendimientos del trabajo - '
             'Rendimientos en especie - Valor percepciones en especie')
    casilla_06 = fields.Float(
        string='[06] Importe de los ingresos a cuenta', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Casilla [06]: Rendimientos del trabajo - '
             'Rendimientos en especie - Importe de los ingresos a cuenta')
    casilla_07 = fields.Integer(
        string='[07] Nº de perceptores', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Casilla [07]: Rendimientos de actividades económicas - '
             'Rendimientos dinerarios - Nº de perceptores')
    casilla_08 = fields.Float(
        string='[08] Importe de las percepciones', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Casilla [08]: Rendimientos de actividades económicas - '
             'Rendimientos dinerarios - Importe de las percepciones')
    casilla_09 = fields.Float(
        string='[09] Importe de las retenciones', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Casilla [09]: Rendimientos de actividades económicas - '
             'Rendimientos dinerarios - Importe de las retenciones')
    casilla_10 = fields.Integer(
        string='[10] Nº de perceptores ', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Casilla [10]: Rendimientos de actividades económicas - '
             'Rendimientos en especie - Nº de perceptores')
    casilla_11 = fields.Float(
        string='[11] Valor percepciones en especie', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Casilla [11]: Rendimientos de actividades económicas - '
             'Rendimientos en especie - Valor percepciones en especie')
    casilla_12 = fields.Float(
        string='[12] Importe de los ingresos a cuenta', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Casilla [12]: Rendimientos de actividades económicas - '
        'Rendimientos en especie - Importe de los ingresos a cuenta')
    casilla_13 = fields.Integer(
        string='[13] Nº de perceptores', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Casilla [13]: Premios por la participación en juegos, '
             'concursos, rifas o combinaciones aleatorias - '
             'Premios en metálico - Nº de perceptores')
    casilla_14 = fields.Float(
        string='[14] Importe de las percepciones', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Casilla [14]: Premios por la participación en juegos, '
             'concursos, rifas o combinaciones aleatorias - '
             'Premios en metálico - Importe de las percepciones')
    casilla_15 = fields.Float(
        string='[15] Importe de las retenciones', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Casilla [15]: Premios por la participación en juegos, '
             'concursos, rifas o combinaciones aleatorias - '
             'Premios en metálico - Importe de las retenciones')
    casilla_16 = fields.Integer(
        string='[16] Nº de perceptores', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Casilla [16]: Premios por la participación en juegos, '
             'concursos, rifas o combinaciones aleatorias - '
             'Premios en especie - Nº de perceptores')
    casilla_17 = fields.Float(
        string='[17] Valor percepciones en especie', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Casilla [17]: Premios por la participación en juegos, '
             'concursos, rifas o combinaciones aleatorias - '
             'Premios en especie - Valor percepciones en especie')
    casilla_18 = fields.Float(
        string='[18] Importe de los ingresos a cuenta', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Casilla [18]: Premios por la participación en juegos, '
             'concursos, rifas o combinaciones aleatorias - '
             'Premios en especie - Importe de los ingresos a cuenta')
    casilla_19 = fields.Integer(
        string='[19] Nº de perceptores', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Casilla [19]: Ganancias patrimoniales derivadas de los '
             'aprovechamientos forestales de los vecinos en montes públicos - '
             'Percepciones dinerarias - Nº de perceptores')
    casilla_20 = fields.Float(
        string='[20] Importe de las percepciones', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Casilla [20]: Ganancias patrimoniales derivadas de los '
             'aprovechamientos forestales de los vecinos en montes públicos - '
             'Percepciones dinerarias - Importe de las percepciones')
    casilla_21 = fields.Float(
        string='[21] Importe de las retenciones', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Casilla [21]: Ganancias patrimoniales derivadas de los '
             'aprovechamientos forestales de los vecinos en montes públicos - '
             'Percepciones dinerarias - Importe de las retenciones')
    casilla_22 = fields.Integer(
        string='[22] Nº de perceptores', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Casilla [22]: Ganancias patrimoniales derivadas de los '
             'aprovechamientos forestales de los vecinos en montes públicos - '
             'Percepciones en especie - Nº de perceptores')
    casilla_23 = fields.Float(
        string='[23] Valor percepciones en especie', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Casilla [23]: Ganancias patrimoniales derivadas de los '
             'aprovechamientos forestales de los vecinos en montes públicos - '
             'Percepciones en especie - Valor percepciones en especie')
    casilla_24 = fields.Float(
        string='[24] Importe de los ingresos a cuenta', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Casilla [24]: Ganancias patrimoniales derivadas de los '
             'aprovechamientos forestales de los vecinos en montes públicos - '
             'Percepciones en especie - Importe de los ingresos a cuenta')
    casilla_25 = fields.Integer(
        string='[25] Nº de perceptores', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Casilla [25]: Contraprestaciones por la cesión de derechos de '
             'imagen: ingresos a cuenta previstos en el artículo 92.8 de la '
             'Ley del Impuesto - Contraprestaciones dinerarias o en especie '
             '- Nº de perceptores')
    casilla_26 = fields.Float(
        string='[26] Contraprestaciones satisfechas', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Casilla [26]: Contraprestaciones por la cesión de derechos de '
             'imagen: ingresos a cuenta previstos en el artículo 92.8 de la '
             'Ley del Impuesto - Contraprestaciones dinerarias o en especie '
             '- Contraprestaciones satisfechas')
    casilla_27 = fields.Float(
        string='[27] Importe de los ingresos a cuenta', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Casilla [27]: Contraprestaciones por la cesión de derechos de '
             'imagen: ingresos a cuenta previstos en el artículo 92.8 de la '
             'Ley del Impuesto - Contraprestaciones dinerarias o en especie '
             '- Importe de los ingresos a cuenta')
    casilla_28 = fields.Float(
        string='[28] Suma de retenciones',
        readonly=True, compute='_compute_28',
        help='Total liquidación - Suma de retenciones e ingresos a cuenta: '
             '([03] + [06] + [09] + [12] + [15] + [18] + [21] + [24] + [27])')
    casilla_29 = fields.Float(
        string='[29] Resultados a ingresar anteriores', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Total liquidación - A deducir (exclusivamente en caso de '
             'autoliquidación complementaria): Resultados a ingresar de '
             'anteriores autoliquidaciones por el mismo concepto, ejercicio '
             'y período')
    casilla_30 = fields.Float(
        string='[30] Resultado a ingresar',
        readonly=True, compute='_compute_30',
        help='Total liquidación - Resultado a ingresar: ([28] - [29])')
    codigo_electronico_anterior = fields.Char(
        string='Código electrónico', size=16, readonly=True,
        states={'draft': [('readonly', False)]},
        help='Código electrónico de la declaración anterior (si se presentó '
        'telemáticamente). A cumplimentar sólo en el caso de declaración '
        'complementaria.')
    currency_id = fields.Many2one(
        comodel_name='res.currency', string='Moneda', readonly=True,
        related='company_id.currency_id', store=True)
    tipo_declaracion = fields.Selection(
        [('I', 'Ingreso'), ('U', 'Domiciliación'),
         ('G', 'Ingreso a anotar en CCT'), ('N', 'Negativa')],
        string='Tipo de declaración', readonly=True,
        states={'draft': [('readonly', False)]}, required=True)
    contact_mobile_phone = fields.Char(
        string="Mobile Phone", size=9,
        states={'calculated': [('required', True)],
                'confirmed': [('readonly', True)]})
    colegio_concertado = fields.Boolean(
        string='Colegio concertado', readonly=True,
        states={'draft': [('readonly', False)]}, default=False)
    move_lines_02 = fields.Many2many(
        comodel_name='account.move.line',
        relation='mod111_account_move_line02_rel',
        column1='mod111', column2='account_move_line')
    move_lines_03 = fields.Many2many(
        comodel_name='account.move.line',
        relation='mod111_account_move_line03_rel',
        column1='mod111', column2='account_move_line')
    move_lines_05 = fields.Many2many(
        comodel_name='account.move.line',
        relation='mod111_account_move_line05_rel',
        column1='mod111', column2='account_move_line')
    move_lines_06 = fields.Many2many(
        comodel_name='account.move.line',
        relation='mod111_account_move_line06_rel',
        column1='mod111', column2='account_move_line')
    move_lines_08 = fields.Many2many(
        comodel_name='account.move.line',
        relation='mod111_account_move_line08_rel',
        column1='mod111', column2='account_move_line')
    move_lines_09 = fields.Many2many(
        comodel_name='account.move.line',
        relation='mod111_account_move_line09_rel',
        column1='mod111', column2='account_move_line')

    @api.one
    @api.constrains('codigo_electronico_anterior', 'previous_number')
    def _check_complementary(self):
        if (self.type == 'C' and
                not self.codigo_electronico_anterior and
                not self.previous_number):
            raise exceptions.Warning(
                _('Si se marca la casilla de liquidación complementaria,'
                  ' debe rellenar el código electrónico o'
                  ' el número de justificante de la declaración anterior.'))

    def __init__(self, pool, cr):
        self._aeat_number = '111'
        super(L10nEsAeatMod111Report, self).__init__(pool, cr)

    @api.multi
    def _get_move_line_domain(self, codes, periods=None,
                              include_children=True):
        domain = super(L10nEsAeatMod111Report, self)._get_move_line_domain(
            codes, periods=periods, include_children=include_children)
        if self.env.context.get('no_partner'):
            return filter(lambda line: line[0] != 'partner_id', domain)
        return domain

    @api.multi
    def calculate(self):
        self.ensure_one()
        # I. Rendimientos del trabajo
        move_lines02 = self.with_context({'no_partner': True}).\
            _get_tax_code_lines(['IRPATBI'], periods=self.periods)
        move_lines03 = self.with_context({'no_partner': True}).\
            _get_tax_code_lines(['IRPATC'], periods=self.periods)
        move_lines05 = self.with_context({'no_partner': True}).\
            _get_tax_code_lines(['IRPTBIE'], periods=self.periods)
        move_lines06 = self.with_context({'no_partner': True}).\
            _get_tax_code_lines(['IRPATCE'], periods=self.periods)
        self.move_lines_02 = move_lines02.ids
        self.move_lines_03 = move_lines03.ids
        self.move_lines_05 = move_lines05.ids
        self.move_lines_06 = move_lines06.ids
        self.casilla_01 = len(
            (move_lines02 + move_lines03).mapped('partner_id'))
        self.casilla_02 = sum(move_lines02.mapped('tax_amount'))
        self.casilla_03 = sum(move_lines03.mapped('tax_amount'))
        self.casilla_04 = len(
            (move_lines05 + move_lines06).mapped('partner_id'))
        self.casilla_05 = sum(move_lines05.mapped('tax_amount'))
        self.casilla_06 = sum(move_lines06.mapped('tax_amount'))
        # II. Rendimientos de actividades económicas
        move_lines08 = self._get_tax_code_lines(
            ['IRPBIAE'], periods=self.periods)
        move_lines09 = self._get_tax_code_lines(
            ['ITRPCAE'], periods=self.periods)
        self.move_lines_08 = move_lines08.ids
        self.move_lines_09 = move_lines09.ids
        self.casilla_08 = sum(move_lines08.mapped('tax_amount'))
        self.casilla_09 = sum(move_lines09.mapped('tax_amount'))
        self.casilla_07 = len(
            (move_lines08 + move_lines09).mapped('partner_id'))
        # III. Premios por la participación en juegos, concursos,
        #      rifas o combinaciones aleatorias
        #      El usuario lo introduce a mano después de calcular
        # IV. Ganancias patrimoniales derivadas de los aprovechamientos
        #     forestales de los vecinos en montes públicos
        #     El usuario lo introduce a mano después de calcular
        # V. Contraprestaciones por la cesión de derechos de imagen:
        #    ingresos a cuenta previstos en el artículo 92.8 de la
        #    Ley del Impuesto
        #    El usuario lo introduce a mano después de calcular

    @api.one
    @api.depends('casilla_03', 'casilla_06', 'casilla_09', 'casilla_12',
                 'casilla_15', 'casilla_18', 'casilla_21', 'casilla_24',
                 'casilla_27')
    def _compute_28(self):
        self.casilla_28 = (
            self.casilla_03 + self.casilla_06 + self.casilla_09 +
            self.casilla_12 + self.casilla_15 + self.casilla_18 +
            self.casilla_21 + self.casilla_24 + self.casilla_27
        )

    @api.one
    @api.depends('casilla_28', 'casilla_29')
    def _compute_30(self):
        self.casilla_30 = self.casilla_28 - self.casilla_29

    @api.multi
    def show_move_lines(self):
        move_lines = []
        if self.env.context.get('move_lines_08', False):
            move_lines = self.move_lines_08.ids
        elif self.env.context.get('move_lines_09', False):
            move_lines = self.move_lines_09.ids
        elif self.env.context.get('move_lines_02', False):
            move_lines = self.move_lines_02.ids
        elif self.env.context.get('move_lines_03', False):
            move_lines = self.move_lines_03.ids
        elif self.env.context.get('move_lines_05', False):
            move_lines = self.move_lines_05.ids
        elif self.env.context.get('move_lines_06', False):
            move_lines = self.move_lines_06.ids
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
