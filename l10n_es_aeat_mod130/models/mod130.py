# -*- encoding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp import models, fields, api, exceptions


def trunc(f, n):
    slen = len('%.*f' % (n, f))
    return float(str(f)[:slen])


class L10nEsAeatMod130Report(models.Model):
    _inherit = "l10n.es.aeat.report"
    _name = "l10n.es.aeat.mod130.report"
    _description = "AEAT 130 report"

    company_partner_id = fields.Many2one('res.partner', string='Partner',
                                         relation='company_id.partner_id',
                                         store=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                         relation='company_id.currency_id',
                                         store=True)
    period = fields.Selection([
            ('1T', 'First quarter'), ('2T', 'Second quarter'),
            ('3T', 'Third quarter'), ('4T', 'Fourth quarter')],
            string='Period', states={'draft': [('readonly', False)]},
            readonly=True, required=True)
    activity_type = fields.Selection([
            ('primary', 'Actividad agrícola, ganadera, forestal o pesquera'),
            ('other', 'Actividad distinta a las anteriores')],
            string='Tipo de actividad',
            states={'draft': [('readonly', False)]},
            readonly=True, required=True, default='other')
    has_deduccion_80 = fields.Boolean(
            string="¿Deducción por art. 80 bis?",
            states={'draft': [('readonly', False)]}, readonly=True,
            help="Permite indicar si puede beneficiarse de la deducción por "
                 "obtención de rendimientos de actividades económicas a "
                 "efectos del pago fraccionado por cumplir el siguiente "
                 "requisito:\n"
                 "Que, en el primer trimestre del ejercicio o en el primer "
                 "trimestre de inicio de actividades, la suma del resultado "
                 "de elevar al año el importe de la casilla 03 y/o, en su "
                 "caso, el resultado de elevar al año el 25 por 100 de la "
                 "casilla 08, sea igual o inferior a 12.000 euros. En los "
                 "supuestos de inicio de la actividad a lo largo del "
                 "ejercicio en la elevación al año se tendrán en "
                 "consideración los días que resten hasta el final del año.",
                 default=False)
    has_prestamo = fields.Boolean(
            string="¿Préstamo para vivienda habitual?",
            states={'draft': [('readonly', False)]}, readonly=True,
            help="Permite indicar si destina cantidades al pago de préstamos "
                 "para la adquisición o rehabilitación de la vivienda "
                 "habitual. Si marca la casilla, se podrá realiza un 2% de "
                 "deducción sobre el importe de la casilla [03], con un "
                 "máximo de 660,14 € por trimestre, o del 2% de la casilla "
                 "[08], con un máximo de 660,14 euros anuales. \nDebe "
                 "consultar las excepciones para las que no se computaría "
                 "la deducción a pesar del préstamo.", default=False)
    complementary = fields.Boolean(
            string="Presentación complementaria",
            states={'draft': [('readonly', False)]}, readonly=True,
            help="Se marcará si esta declaración es complementaria de "
                 "otra u otras declaraciones presentadas anteriormente "
                 "por el mismo concepto y correspondientes al mismo "
                 "ejercicio y período.", default=False)
    previous_electronic_code = fields.Char(
            string="Cód. electr. declaración anterior", size=16,
            help="Código electrónico de la declaración anterior (si se "
                 "presentó telemáticamente). A cumplimentar sólo en el caso "
                 "de declaración complementaria", readonly=False,
                 states={'done': [('readonly', True)]})
    comments = fields.Char(
            string="Observaciones", size=350, readonly=True,
            help="Observaciones que se adjuntarán con el modelo",
            states={'draft': [('readonly', False)]})
    casilla_01 = fields.Float(string="Casilla [01] - Ingresos", readonly=True)
    casilla_02 = fields.Float(string="Casilla [02] - Gastos", readonly=True)
    casilla_03 = fields.Float(string="Casilla [03] - Rendimiento",
                              readonly=True)
    casilla_04 = fields.Float(string="Casilla [04] - IRPF", readonly=True)
    casilla_05 = fields.Float(string="Casilla [05]", readonly=True)
    casilla_06 = fields.Float(string="Casilla [06]", readonly=True)
    casilla_07 = fields.Float(string="Casilla [07]", readonly=True)
    casilla_08 = fields.Float(string="Casilla [08] - Ingresos primario",
                                   readonly=True)
    casilla_09 = fields.Float(string="Casilla [09] - IRPF primario",
                                   readonly=True)
    casilla_10 = fields.Float(string="Casilla [10]", readonly=True)
    casilla_11 = fields.Float(string="Casilla [11]", readonly=True)
    casilla_12 = fields.Float(string="Casilla [12]", readonly=True)
    casilla_13 = fields.Float(string="Casilla [13] - Deducción art. 80 bis",
                                   readonly=True)
    casilla_14 = fields.Float(string="Casilla [14]", readonly=True)
    casilla_15 = fields.Float(string="Casilla [15]", readonly=True)
    casilla_16 = fields.Float(string="Casilla [16] - Deducción por pago "
                                   "de hipoteca", readonly=True)
    casilla_17 = fields.Float(string="Casilla [17]", readonly=True)
    casilla_18 = fields.Float(string="Casilla [18]", readonly=True)
    result = fields.Float(string="Resultado", readonly=True)
    tipo_declaracion = fields.Selection([('I', 'A ingresar'),
                                        ('N', 'Negativa'),
                                        ('B', 'A deducir')],
                                        string='Tipo declaración',
                                        readonly=True)
    number = fields.Char(default='130')

    @api.constrains('previous_electronic_code', 'previous_number')
    def check_complementary(self):
        for report in self:
            if (report.complementary and
                    not report.previous_electronic_code and
                    not report.previous_number):
                raise exceptions.Warning('Si se marca la casilla de '
                                         'liquidación complementaria, debe '
                                         'rellenar el código electrónico o el '
                                         'nº de justifacnte de la declaración '
                                         'anterior.')

    @api.onchange('casilla_18', 'casilla_17')
    def onchange_casilla_18(self):
        self.result = self.casilla_17 - self.casilla_18

    @api.multi
    def _get_periods(self, period):
        self.ensure_one()
        """
        Obtiene el periodo o periodos contables asociados al trimestre del
        informe asociado.
        """
        period_obj = self.env["account.period"]
        year = self.fiscalyear_id.date_start.split('-')[0]
        # Obtener el primer mes del trimestre
        month = int(period[0]) * 3 - 2
        fecha_ini = datetime.strptime('%s-%s-01' % (year, month), '%Y-%m-%d')
        fecha_fin = fecha_ini + relativedelta(months=3, days=-1)
        account_period_ids = period_obj.search(
            [('date_start', '>=', fecha_ini),
             ('date_stop', '<=', fecha_fin),
             ('company_id', '=', self.company_id.id)])
        if not account_period_ids:
            raise exceptions.Warning(
                "No se ha encontrado un periodo "
                "contable adecuado para el periodo y ejercicio fiscal "
                "indicados. Revise si tiene especificado en el periodo el "
                "trimestre al que pertenece.")
        return account_period_ids.ids

    @api.multi
    def _calc_ingresos_gastos(self):
        self.ensure_one()
        periods = ['1T', '2T', '3T', '4T']
        income_accounts = ['7']
        expense_accounts = ['6']
        period_ids = []
        for period in periods:
            period_ids += self._get_periods(period)
            if period == self.period:
                break
        acc_obj = self.env['account.account'].with_context(
            fiscalyear=self.fiscalyear_id.id, periods=period_ids)
        income_account_ids = acc_obj.search(
            [('code', 'in', income_accounts),
             ('company_id', '=', self.company_id.id)])
        ingresos = sum([-x.balance for x in income_account_ids])
        expense_account_ids = acc_obj.search([('code', 'in', expense_accounts),
                                              ('company_id', '=',
                                               self.company_id.id)])
        gastos = sum([x.balance for x in expense_account_ids])
        return (ingresos, gastos)

    @api.multi
    def _calc_prev_trimesters_data(self):
        self.ensure_one()
        periods = ['1T', '2T', '3T', '4T']
        amount = 0
        for period in periods:
            if period == self.period:
                break
            report_ids = self.search(
                [('period', '=', period),
                 ('fiscalyear_id', '=', self.fiscalyear_id.id),
                 ('company_id', '=', self.company_id.id)])
            if not report_ids:
                raise exceptions.Warning(
                    "No se ha encontrado la "
                    "declaración mod. 130 para el trimestre %s. No se "
                    "puede continuar el cálculo si no existe dicha "
                    "declaración." % period)
            prev_report = report_ids[0]
            if prev_report.casilla_07 > 0:
                amount += prev_report.casilla_07 - prev_report.casilla_16
        return amount

    @api.multi
    def calculate(self):
        for report in self:
            if report.activity_type == 'primary':
                raise exceptions.Warning('Este tipo de actividad no '
                                         'está aún soportado por el módulo.')
            if report.has_deduccion_80:
                raise exceptions.Warning(
                    'No se pueden calcular por el '
                    'momento declaraciones que contengan deducciones por el '
                    'artículo 80 bis.')
            vals = {}
            if report.activity_type == 'other':
                ingresos, gastos = report._calc_ingresos_gastos()
                vals['casilla_01'] = ingresos
                vals['casilla_02'] = gastos
                # Rendimiento
                vals['casilla_03'] = ingresos - gastos
                if vals['casilla_03'] < 0:
                    vals['casilla_03'] = 0.0
                # IRPF - Truncar resultado, ya que es lo que hace la AEAT
                vals['casilla_04'] = trunc(0.20 * vals['casilla_03'], 2)
                # Pago fraccionado previo del trimestre
                vals['casilla_05'] = report._calc_prev_trimesters_data()
                vals['casilla_06'] = 0.0
                vals['casilla_07'] = (vals['casilla_04'] - vals['casilla_05'] -
                                      vals['casilla_06'])
                vals['casilla_12'] = vals['casilla_07']
                if vals['casilla_12'] < 0:
                    vals['casilla_12'] = 0.0
            else:
                # TODO: Modelo 130 para actividades primarias
                vals['casilla_12'] = vals['casilla_11']
            # TODO: Deducción artículo 80 bis
            vals['casilla_13'] = 0.0
            vals['casilla_14'] = vals['casilla_12'] - vals['casilla_13']
            # TODO: Poner los resultados negativos de anteriores trimestres
            vals['casilla_15'] = 0.0
            # Deducción por hipóteca
            if report.has_prestamo and vals['casilla_14'] > 0:
                # Truncar resultado, ya que es lo que hace la AEAT
                deduccion = trunc(0.02 * vals['casilla_03'], 2)
                if report.activity_type == 'other':
                    if deduccion > 660.14:
                        deduccion = 660.14
                else:
                    raise orm.except_orm('No implementado')
                dif = vals['casilla_14'] - vals['casilla_15']
                if deduccion > dif:
                    deduccion = dif
                vals['casilla_16'] = deduccion
            else:
                vals['casilla_16'] = 0.0
            vals['casilla_17'] = (vals['casilla_14'] - vals['casilla_15'] -
                                  vals['casilla_16'])
            if report.complementary:
                vals['result'] = vals['casilla_17'] - report.casilla_18
            else:
                vals['casilla_18'] = 0.0
                vals['result'] = vals['casilla_17']
            if vals['result'] < 0 and report.period != '4T':
                vals['tipo_declaracion'] = "B"
            elif report.result < 0:
                vals['tipo_declaracion'] = "N"
            else:
                vals['tipo_declaracion'] = "I"
            report.write(vals)
        return True

    @api.multi
    def button_confirm(self):
        """Check its records"""
        msg = ""
        for report in self:
            if report.complementary:
                if not report.casilla_18:
                    msg = ('Debe introducir una cantidad en la casilla 18 '
                           'como ha marcado la casilla de declaración '
                           'complementaria.')
                if (report.previous_electronic_code and
                        len(report.previous_electronic_code) < 16):
                    msg = ('El código electrónico de la declaración anterior '
                           'debe tener 16 caracteres.')
                if (report.previous_number and
                        len(report.previous_number) < 13):
                    msg = ('El nº de justificante de la declaración anterior '
                           'debe tener 13 caracteres.')
        if msg:
            raise exceptions.Warning(msg)
        return super(L10nEsAeatMod130Report, self).button_confirm()
