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
                                help='Rendim. del trabajo - Rendimientos '
                                'dinerarios - Nº de perceptores')
    casilla_02 = fields.Float('Casilla [02]', readonly=True,
                              help='Rendim. del trabajo - Rendimientos '
                              'dinerarios - Importe percepciones')
    casilla_03 = fields.Float('Casilla [03]', readonly=True,
                              help='Rendim. del trabajo - Rendimientos '
                              'dinerarios - Importe retenciones')
    casilla_04 = fields.Integer('Casilla [04]', readonly=True,
                                help='Rendim. del trabajo - Rendimientos '
                                'en especie - Nº de perceptores')
    casilla_05 = fields.Float('Casilla [05]', readonly=True,
                              help='Rendim. del trabajo - Rendimientos '
                              'en especie - Valor percepciones en especie')
    casilla_06 = fields.Float('Casilla [06]', readonly=True,
                              help='Rendim. del trabajo - Rendimientos '
                              'en especie - Importe ingresos en cuenta')
    casilla_07 = fields.Integer('Casilla [07]', readonly=True,
                                help='Rendim. actividades económicas - '
                                'Rendimientos dinerarios - Nº de perceptores')
    casilla_08 = fields.Float('Casilla [08]', readonly=True,
                              help='Rendim. actividades económicas - '
                              'Rendimientos dinerarios - Importe percepciones')
    casilla_09 = fields.Float('Casilla [09]', readonly=True,
                              help='Rendim. actividades económicas - '
                              'Rendimientos dinerarios - Importe retenciones')
    casilla_10 = fields.Integer('Casilla [10]', readonly=True,
                                help='Rendim. actividades económicas - '
                                'Rendimientos en especie - Nº de perceptores')
    casilla_11 = fields.Float('Casilla [11]', readonly=True,
                              help='Rendim. actividades económicas - '
                              'Rendimientos en especie - Valor percepciones en'
                              ' especie')
    casilla_12 = fields.Float('Casilla [12]', readonly=True,
                              help='Rendim. actividades económicas - '
                              'Rendimientos en especie - Importe de los '
                              'ingresos en cuenta')
    casilla_13 = fields.Integer('Casilla [13]', readonly=True,
                                help='Premios - Premios dinerarios - Nº de '
                                'perceptores')
    casilla_14 = fields.Float('Casilla [14]', readonly=True,
                              help='Premios - Premios dinerarios - Importe de '
                              'las percepciones')
    casilla_15 = fields.Float('Casilla [15]', readonly=True,
                              help='Premios - Premios dinerarios - Importe de '
                              'las retenciones')
    casilla_16 = fields.Integer('Casilla [16]', readonly=True,
                                help='Premios - Premios en especie - Nº de '
                                'perceptores')
    casilla_17 = fields.Float('Casilla [17]', readonly=True,
                              help='Premios - Premios en especie - Importe de '
                              'las percepciones')
    casilla_18 = fields.Float('Casilla [18]', readonly=True,
                              help='Premios - Premios en especie - Importe de '
                              'los ingresos a cuenta')
    casilla_19 = fields.Integer('Casilla [19]', readonly=True,
                                help='Ganancias patrim. Aprovecham. Forestales'
                                ' - Percep. dinerarias - Nº perceptores')
    casilla_20 = fields.Float('Casilla [20]', readonly=True,
                              help='Ganancias patrim. Aprovecham. Forestales'
                              ' - Percep. dinerarias - Importe percepciones')
    casilla_21 = fields.Float('Casilla [21]', readonly=True,
                              help='Ganancias patrim. Aprovecham. Forestales'
                              ' - Percep. dinerarias - Importe retenciones')
    casilla_22 = fields.Integer('Casilla [22]', readonly=True,
                                help='Ganancias patrim. Aprovecham. Forestales'
                                ' - Percep. en especie - Nº perceptores')
    casilla_23 = fields.Float('Casilla [23]', readonly=True,
                              help='Ganancias patrim. Aprovecham. Forestales -'
                              ' Percep. en especie - Importe percepciones')
    casilla_24 = fields.Float('Casilla [24]', readonly=True,
                              help='Ganancias patrim. Aprovecham. Forestales'
                              ' - Percep. en especie - Importe ingresos a '
                              'cuenta')
    casilla_25 = fields.Integer('Casilla [25]', readonly=True,
                                help='Contraprest. cesión dchos. imagen - Nº '
                                'de perceptores')
    casilla_26 = fields.Float('Casilla [26]', readonly=True,
                              help='Contraprest. cesión dchos. imagen - '
                              'Contraprestaciones satisfechas')
    casilla_27 = fields.Float('Casilla [27]', readonly=True,
                              help='Contraprest. cesión dchos. imagen - '
                              'Importe de los ingresos a cuenta')
    casilla_28 = fields.Float('Casilla [28]', readonly=True,
                              help='Total liquidación - Suma retencones e '
                              'ingresos a cuenta')
    casilla_29 = fields.Float('Casilla [29]', readonly=True,
                              help='Total liquidación - Resultado de '
                              'anteriores declaraciones')
    casilla_30 = fields.Float('Casilla [30]', readonly=True,
                              help='Total liquidación - Resultado a ingresar')
    codigo_electronico_anterior = fields.Char(
        'Código electrónico', size=16, readonly=True,
        states={'draft': [('readonly', False)]},
        help='Código electrónico de la declaración anterior (si se presentó '
        'telemáticamente). A cumplimentar sólo en el caso de declaración '
        'complementaria.')
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
    contact_mobile_phone = fields.Char(
        string="Mobile Phone", size=9,
        states={'calculated': [('required', True)],
                'confirmed': [('readonly', True)]})
    colegio_concertado = fields.Boolean('Colegio Concertado', readonly=True,
                                        states={'draft': [('readonly',
                                                           False)]},
                                        default=False)

    @api.one
    @api.constrains('codigo_electronico_anterior', 'previous_number')
    def _check_complementary(self):
        if (self.type == 'C'
                and not self.codigo_electronico_anterior
                and not self.previous_number):
            raise exceptions.Warning(
                _('Si se marca la casilla de liquidación complementaria,'
                  ' debe rellenar el código electrónico o'
                  ' el número de justificante de la declaración anterior.'))

    def __init__(self, pool, cr):
        self._aeat_number = '111'
        super(L10nEsAeatMod111Report, self).__init__(pool, cr)

    @api.multi
    def get_account_child_ids(self, cuenta, company_id):
        """
        Para una determinada cuenta (tipo str) y compañía, devuelve sus hijas
        (ids) Ejemplo cuentas_hijas = get_account_child_ids('4100')
        """
        account_model = self.env['account.account']
        cuenta_lst = account_model.search([('code', '=', cuenta),
                                           ('company_id', '=', company_id)])
        cuentas_hijas = []
        for cuenta in cuenta_lst:
            cuentas_hijas.extend(cuenta.child_id.ids)
        return cuentas_hijas

    @api.multi
    def get_actividades_economicas(self, period_id, company_id):
        """
         Recorrer apuntes contables, para el período dado (inherente el
          ejercicio fiscal) y para los diarios del tipo compras, para obtener
          rendimientos actividades económicas además, sólo los referentes al
          código de cuenta 4751 para la base imponible, sobre cada apunte
          contable de la 4751, acudir al asiento para obtener el valor del
          campo haber (credit) del apunte contra la cuenta padre 4100 y sus
          hijas
        """
        move_line_model = self.env['account.move.line']
        journal_model = self.env['account.journal']
        cuentas_hijas_4751 = self.get_account_child_ids('4751', company_id.id)
        journal_ids = journal_model.search(
            ['|', ('type', '=', 'purchase'), ('type', '=', 'purchase_refund'),
             ('company_id', '=', company_id.id)])
        move_line_4751_ids = move_line_model.search(
            [('period_id', '=', period_id.id),
             ('account_id', 'in', cuentas_hijas_4751),
             ('journal_id', 'in', journal_ids.ids)])
        partners = []
        importes = 0.0
        base_imponible = 0.0
        for move in move_line_4751_ids:
            if move.partner_id not in partners:
                partners.append(move.partner_id)
            importes += move.tax_amount
            cuentas_hijas_4100 = self.get_account_child_ids('4100',
                                                            company_id.id)
            move_line_4100_hijas_ids = move_line_model.search([
                ('move_id', '=', move.move_id.id),
                ('account_id', 'in', cuentas_hijas_4100)])
            for move4100 in move_line_4100_hijas_ids:
                base_imponible += move4100.credit
        return partners, base_imponible, importes

    @api.multi
    def calculate(self):
        self.ensure_one()
        ae_partners, ae_base_imponible, ae_tax_amount = (
            self.get_actividades_economicas(self.period_id, self.company_id))
        vals = {}
        vals['casilla_07'] = len(ae_partners)
        vals['casilla_08'] = abs(ae_base_imponible)
        vals['casilla_09'] = abs(ae_tax_amount)
        self.write(vals)
