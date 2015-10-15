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


class L10nEsAeatMod111Report(models.Model):

    _description = 'AEAT 111 report'
    _inherit = 'l10n.es.aeat.report'
    _name = 'l10n.es.aeat.mod111.report'

    number = fields.Char(default='111')
    casilla_01 = fields.Integer('Casilla [01]', readonly=True,
                                states={'calculated': [('readonly', False)]},
                                help='Rendim. del trabajo - Rendimientos '
                                'dinerarios - Nº de perceptores')
    casilla_02 = fields.Float('Casilla [02]', readonly=True,
                              states={'calculated': [('readonly', False)]},
                              help='Rendim. del trabajo - Rendimientos '
                              'dinerarios - Importe percepciones')
    casilla_03 = fields.Float('Casilla [03]', readonly=True,
                              states={'calculated': [('readonly', False)]},
                              help='Rendim. del trabajo - Rendimientos '
                              'dinerarios - Importe retenciones')
    casilla_04 = fields.Integer('Casilla [04]', readonly=True,
                                states={'calculated': [('readonly', False)]},
                                help='Rendim. del trabajo - Rendimientos '
                                'en especie - Nº de perceptores')
    casilla_05 = fields.Float('Casilla [05]', readonly=True,
                              states={'calculated': [('readonly', False)]},
                              help='Rendim. del trabajo - Rendimientos '
                              'en especie - Valor percepciones en especie')
    casilla_06 = fields.Float('Casilla [06]', readonly=True,
                              states={'calculated': [('readonly', False)]},
                              help='Rendim. del trabajo - Rendimientos '
                              'en especie - Importe ingresos en cuenta')
    casilla_07 = fields.Integer('Casilla [07]', readonly=True,
                                states={'calculated': [('readonly', False)]},
                                help='Rendim. actividades económicas - '
                                'Rendimientos dinerarios - Nº de perceptores')
    casilla_08 = fields.Float('Casilla [08]', readonly=True,
                              states={'calculated': [('readonly', False)]},
                              help='Rendim. actividades económicas - '
                              'Rendimientos dinerarios - Importe percepciones')
    casilla_09 = fields.Float('Casilla [09]', readonly=True,
                              states={'calculated': [('readonly', False)]},
                              help='Rendim. actividades económicas - '
                              'Rendimientos dinerarios - Importe retenciones')
    casilla_10 = fields.Integer('Casilla [10]', readonly=True,
                                states={'calculated': [('readonly', False)]},
                                help='Rendim. actividades económicas - '
                                'Rendimientos en especie - Nº de perceptores')
    casilla_11 = fields.Float('Casilla [11]', readonly=True,
                              states={'calculated': [('readonly', False)]},
                              help='Rendim. actividades económicas - '
                              'Rendimientos en especie - Valor percepciones en'
                              ' especie')
    casilla_12 = fields.Float('Casilla [12]', readonly=True,
                              states={'calculated': [('readonly', False)]},
                              help='Rendim. actividades económicas - '
                              'Rendimientos en especie - Importe de los '
                              'ingresos en cuenta')
    casilla_13 = fields.Integer('Casilla [13]', readonly=True,
                                states={'calculated': [('readonly', False)]},
                                help='Premios - Premios dinerarios - Nº de '
                                'perceptores')
    casilla_14 = fields.Float('Casilla [14]', readonly=True,
                              states={'calculated': [('readonly', False)]},
                              help='Premios - Premios dinerarios - Importe de '
                              'las percepciones')
    casilla_15 = fields.Float('Casilla [15]', readonly=True,
                              states={'calculated': [('readonly', False)]},
                              help='Premios - Premios dinerarios - Importe de '
                              'las retenciones')
    casilla_16 = fields.Integer('Casilla [16]', readonly=True,
                                states={'calculated': [('readonly', False)]},
                                help='Premios - Premios en especie - Nº de '
                                'perceptores')
    casilla_17 = fields.Float('Casilla [17]', readonly=True,
                              states={'calculated': [('readonly', False)]},
                              help='Premios - Premios en especie - Importe de '
                              'las percepciones')
    casilla_18 = fields.Float('Casilla [18]', readonly=True,
                              states={'calculated': [('readonly', False)]},
                              help='Premios - Premios en especie - Importe de '
                              'los ingresos a cuenta')
    casilla_19 = fields.Integer('Casilla [19]', readonly=True,
                                states={'calculated': [('readonly', False)]},
                                help='Ganancias patrim. Aprovecham. Forestales'
                                ' - Percep. dinerarias - Nº perceptores')
    casilla_20 = fields.Float('Casilla [20]', readonly=True,
                              states={'calculated': [('readonly', False)]},
                              help='Ganancias patrim. Aprovecham. Forestales'
                              ' - Percep. dinerarias - Importe percepciones')
    casilla_21 = fields.Float('Casilla [21]', readonly=True,
                              states={'calculated': [('readonly', False)]},
                              help='Ganancias patrim. Aprovecham. Forestales'
                              ' - Percep. dinerarias - Importe retenciones')
    casilla_22 = fields.Integer('Casilla [22]', readonly=True,
                                states={'calculated': [('readonly', False)]},
                                help='Ganancias patrim. Aprovecham. Forestales'
                                ' - Percep. en especie - Nº perceptores')
    casilla_23 = fields.Float('Casilla [23]', readonly=True,
                              states={'calculated': [('readonly', False)]},
                              help='Ganancias patrim. Aprovecham. Forestales -'
                              ' Percep. en especie - Importe percepciones')
    casilla_24 = fields.Float('Casilla [24]', readonly=True,
                              states={'calculated': [('readonly', False)]},
                              help='Ganancias patrim. Aprovecham. Forestales'
                              ' - Percep. en especie - Importe ingresos a '
                              'cuenta')
    casilla_25 = fields.Integer('Casilla [25]', readonly=True,
                                states={'calculated': [('readonly', False)]},
                                help='Contraprest. cesión dchos. imagen - Nº '
                                'de perceptores')
    casilla_26 = fields.Float('Casilla [26]', readonly=True,
                              states={'calculated': [('readonly', False)]},
                              help='Contraprest. cesión dchos. imagen - '
                              'Contraprestaciones satisfechas')
    casilla_27 = fields.Float('Casilla [27]', readonly=True,
                              states={'calculated': [('readonly', False)]},
                              help='Contraprest. cesión dchos. imagen - '
                              'Importe de los ingresos a cuenta')
    casilla_28 = fields.Float('Casilla [28]', readonly=True,
                              states={'calculated': [('readonly', False)]},
                              help='Total liquidación - Suma retencones e '
                              'ingresos a cuenta')
    casilla_29 = fields.Float('Casilla [29]', readonly=True,
                              states={'calculated': [('readonly', False)]},
                              help='Total liquidación - Resultado de '
                              'anteriores declaraciones')
    casilla_30 = fields.Float('Casilla [30]', readonly=True,
                              states={'calculated': [('readonly', False)]},
                              help='Total liquidación - Resultado a ingresar')
    codigo_electronico_anterior = fields.Char(
        'Código electrónico', size=16, readonly=True,
        states={'draft': [('readonly', False)]},
        help='Código electrónico de la declaración anterior (si se presentó '
        'telemáticamente). A cumplimentar sólo en el caso de declaración '
        'complementaria.')
    currency_id = fields.Many2one('res.currency', string='Moneda',
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
    colegio_concertado = fields.Boolean('Colegio concertado', readonly=True,
                                        states={'draft': [('readonly',
                                                           False)]},
                                        default=False)
    move_lines_08 = fields.Many2many(comodel_name='account.move.line',
                                     relation='mod111_account_move_line08_rel',
                                     column1='mod111',
                                     column2='account_move_line')
    move_lines_09 = fields.Many2many(comodel_name='account.move.line',
                                     relation='mod111_account_move_line09_rel',
                                     column1='mod111',
                                     column2='account_move_line')

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
    def calculate(self):
        self.ensure_one()
        tax_code_obj = self.env['account.tax.code']
        tax_code = tax_code_obj.search([('code', '=', 'IRPBI')])
        if not tax_code:
            raise exceptions.Warning(_('Tabla de impuestos desactualizada.'))
        move_lines08 = self._get_tax_code_lines(tax_code, periods=self.periods)
        tax_code = tax_code_obj.search([('code', '=', 'ITRPC')])
        if not tax_code:
            raise exceptions.Warning(_('Tabla de impuestos desactualizada.'))
        move_lines09 = self._get_tax_code_lines(tax_code, periods=self.periods)
        self.move_lines_08 = move_lines08.ids
        self.move_lines_09 = move_lines09.ids
        self.casilla_08 = sum([x.tax_amount for x in move_lines08])
        self.casilla_09 = sum([x.tax_amount for x in move_lines09])
        self.casilla_07 = len(set([x.partner_id for x in (move_lines08 +
                                                          move_lines09)]))
