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
from openerp.osv import orm, fields
from openerp.tools.translate import _

def trunc(f, n):
    slen = len('%.*f' % (n, f))
    return float(str(f)[:slen])

class l10n_es_aeat_mod130_report(orm.Model):
    _inherit = "l10n.es.aeat.report"
    _name = "l10n.es.aeat.mod130.report"
    _description = "AEAT 130 report"

    _columns = {
        'company_partner_id': fields.related('company_id', 'partner_id',
                type='many2one', relation='res.partner', string='Partner',
                store=True),
        'currency_id': fields.related('company_id', 'currency_id',
                type='many2one', relation='res.currency', string='Currency',
                store=True),
        'period': fields.selection(
                [('1T', 'First quarter'), ('2T', 'Second quarter'),
                 ('3T', 'Third quarter'), ('4T', 'Fourth quarter')],
                'Period', states={'draft': [('readonly', False)]},
                readonly=True, required=True),
        'activity_type': fields.selection(
            [('primary', 'Actividad agrícola, ganadera, forestal o pesquera'),
             ('other', 'Actividad distinta a las anteriores')],
            'Tipo de actividad', states={'draft': [('readonly', False)]},
            readonly=True, required=True),
        'has_deduccion_80': fields.boolean(
            "¿Deducción por art. 80 bis?",
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
                 "consideración los días que resten hasta el final del año."),
        'has_prestamo': fields.boolean(
            "¿Préstamo para vivienda habitual?",
            states={'draft': [('readonly', False)]}, readonly=True,
            help="Permite indicar si destina cantidades al pago de préstamos "
                 "para la adquisición o rehabilitación de la vivienda "
                 "habitual. Si marca la casilla, se podrá realiza un 2% de "
                 "deducción sobre el importe de la casilla [03], con un "
                 "máximo de 660,14 € por trimestre, o del 2% de la casilla "
                 "[08], con un máximo de 660,14 euros anuales. \nDebe "
                 "consultar las excepciones para las que no se computaría "
                 "la deducción a pesar del préstamo."),
        'complementary': fields.boolean("Presentación complementaria",
                states={'draft': [('readonly', False)]}, readonly=True,
                help="Se marcará si esta declaración es complementaria de "
                     "otra u otras declaraciones presentadas anteriormente "
                     "por el mismo concepto y correspondientes al mismo "
                     "ejercicio y período."),
        'previous_electronic_code': fields.char(
            "Cód. electr. declaración anterior", size=16,
            help="Código electrónico de la declaración anterior (si se "
                 "presentó telemáticamente). A cumplimentar sólo en el caso "
                 "de declaración complementaria", readonly=False,
                 states={'done': [('readonly', True)]}),
        'previous_number': fields.char("Nº declaración anterior", size=13,
            help="Número de justificante de la declaración anterior (si se "
                 "presentó en papel. A cumplimentar sólo en el caso de "
                 "declaración complementaria", readonly=False,
                 states={'done': [('readonly', True)]}),
        'comments': fields.char("Observaciones", size=350, readonly=True,
            help="Observaciones que se adjuntarán con el modelo",
                 states={'draft': [('readonly', False)]}),
        'casilla_01': fields.float("Casilla [01] - Ingresos", readonly=True),
        'casilla_02': fields.float("Casilla [02] - Gastos", readonly=True),
        'casilla_03': fields.float("Casilla [03] - Rendimiento",
                                   readonly=True),
        'casilla_04': fields.float("Casilla [04] - IRPF", readonly=True),
        'casilla_05': fields.float("Casilla [05]", readonly=True),
        'casilla_06': fields.float("Casilla [06]", readonly=True),
        'casilla_07': fields.float("Casilla [07]", readonly=True),
        'casilla_08': fields.float("Casilla [08] - Ingresos primario",
                                   readonly=True),
        'casilla_09': fields.float("Casilla [09] - IRPF primario",
                                   readonly=True),
        'casilla_10': fields.float("Casilla [10]", readonly=True),
        'casilla_11': fields.float("Casilla [11]", readonly=True),
        'casilla_12': fields.float("Casilla [12]", readonly=True),
        'casilla_13': fields.float("Casilla [13] - Deducción art. 80 bis",
                                   readonly=True),
        'casilla_14': fields.float("Casilla [14]", readonly=True),
        'casilla_15': fields.float("Casilla [15]", readonly=True),
        'casilla_16': fields.float("Casilla [16] - Deducción por pago de "
                                   "hipoteca", readonly=True),
        'casilla_17': fields.float("Casilla [17]", readonly=True),
        'casilla_18': fields.float("Casilla [18]", readonly=True),
        'result': fields.float("Resultado", readonly=True),
        'tipo_declaracion': fields.selection(
                [('I', 'A ingresar'),
                 ('N', 'Negativa'),
                 ('B', 'A deducir')],
                'Tipo declaración', readonly=True),
    }

    def _check_complementary(self, cr, uid, ids, context=None):
        for report in self.read(cr, uid, ids, ['complementary',
                                               'previous_electronic_code',
                                               'previous_number'],
                                context=context):
            if (report['complementary'] and
                    not report['previous_electronic_code'] and
                    not report['previous_number']):
                return False
        return True

    _constraints = [
        (_check_complementary,
         'Si se marca la casilla de liquidación complementaria, debe rellenar '
         'el código electrónico o el nº de justifacnte de la declaración '
         'anterior.', ['previous_electronic_code', 'previous_number']),
    ]

    _defaults = {
        'number': '130',
        'activity_type': 'other',
        'complementary': False,
        'has_prestamo': False,
        'has_deduccion_80': False,
    }

    def onchange_casilla_18(self, cr, uid, ids, casilla_18, casilla_17,
                            context=None):
        return {'value': {'result': casilla_17 - casilla_18}}

    def _get_periods(self, cr, uid, period, report, context=None):
        """
        Obtiene el periodo o periodos contables asociados al trimestre del
        informe asociado.
        """
        period_obj = self.pool["account.period"]
        quarter_dict = {
            "1T": 'first',
            "2T": 'second',
            "3T": 'third',
            "4T": 'fourth',
        }
        year = report.fiscalyear_id.date_start.split('-')[0]
        # Obtener el primer mes del trimestre
        month = int(period[0]) * 3 - 2
        fecha_ini = datetime.strptime('%s-%s-01' %(year, month), '%Y-%m-%d')
        fecha_fin = fecha_ini + relativedelta(months=3, days=-1)
        account_period_ids = period_obj.search(cr, uid,
                                [('date_start', '=', fecha_ini),
                                 ('date_stop', '=', fecha_fin),
                                 ('company_id', '=', report.company_id.id)],
                                    context=context)
        if not account_period_ids:
            account_period_ids = period_obj.search(cr, uid,
                        [('quarter', '=', quarter_dict[period]),
                         ('company_id', '=', report.company_id.id)],
                        context=context)
        if not account_period_ids:
            raise orm.except_orm("Error", "No se ha encontrado un periodo "
                "contable adecuado para el periodo y ejercicio fiscal "
                "indicados. Revise si tiene especificado en el periodo el "
                "trimestre al que pertenece.")
        return account_period_ids

    def _calc_ingresos_gastos(self, cr, uid, report, context=None):
        periods = ['1T', '2T', '3T', '4T']
        income_accounts = ['7']
        expense_accounts = ['6']
        period_ids = []
        for period in periods:
            period_ids += self._get_periods(cr, uid, period, report,
                                            context=context)
            if period == report.period:
                break
        ingresos = 0
        gastos = 0
        acc_obj = self.pool['account.account']
        ctx = context.copy()
        ctx['fiscalyear'] = report.fiscalyear_id.id
        ctx['periods'] = period_ids
        income_account_ids = acc_obj.search(cr, uid,
                                [('code', 'in', income_accounts),
                                 ('company_id','=', report.company_id.id)],
                                context=context)
        for account in acc_obj.browse(cr, uid, income_account_ids,
                                      context=ctx):
            ingresos -= account.balance
        expense_account_ids = acc_obj.search(cr, uid,
                                [('code', 'in', expense_accounts),
                                 ('company_id','=', report.company_id.id)],
                                context=context)
        for account in acc_obj.browse(cr, uid, expense_account_ids,
                                      context=ctx):
            gastos += account.balance
        return (ingresos, gastos)

    def _calc_prev_trimesters_data(self, cr, uid, report, context=None):
        periods = ['1T', '2T', '3T', '4T']
        income_accounts = ['7']
        expense_accounts = ['6']
        amount = 0
        for period in periods:
            if period == report.period:
                break
            report_ids = self.search(cr, uid,
                        [('period', '=', period),
                         ('fiscalyear_id', '=', report.fiscalyear_id.id),
                         ('company_id', '=', report.company_id.id)],
                        context=context)
            if not report_ids:
                raise orm.except_orm("Error", "No se ha encontrado la "
                        "declaración mod. 130 para el trimestre %s. No se "
                        "puede continuar el cálculo si no existe dicha "
                        "declaración." %period)
            prev_report = self.browse(cr, uid, report_ids[0], context=context)
            if prev_report.casilla_07 > 0:
                amount += prev_report.casilla_07 - prev_report.casilla_16
        return amount

    def calculate(self, cr, uid, ids, context=None):
        for report in self.browse(cr, uid, ids, context=context):
            if report.activity_type == 'primary':
                raise orm.except_orm("Error", 'Este tipo de actividad no '
                                     'está aún soportado por el módulo.')
            if report.has_deduccion_80:
                raise orm.except_orm("Error", 'No se pueden calcular por el '
                    'momento declaraciones que contengan deducciones por el '
                    'artículo 80 bis.')
            vals = {}
            if report.activity_type == 'other':
                ingresos, gastos = self._calc_ingresos_gastos(cr, uid, report,
                                                              context=context)
                vals['casilla_01'] = ingresos
                vals['casilla_02'] = gastos
                # Rendimiento
                vals['casilla_03'] = ingresos - gastos
                if vals['casilla_03'] < 0:
                    vals['casilla_03'] = 0.0
                # IRPF - Truncar resultado, ya que es lo que hace la AEAT
                vals['casilla_04'] = trunc(0.20 * vals['casilla_03'], 2)
                # Pago fraccionado previo del trimestre
                vals['casilla_05'] = self._calc_prev_trimesters_data(cr, uid,
                                                    report, context=context)
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
            self.write(cr, uid, report.id, vals, context=context)
        return True

    def button_confirm(self, cr, uid, ids, context=None):
        """Check its records"""
        msg = ""
        for report in self.browse(cr, uid, ids, context=context):
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
            raise orm.except_orm("Error", msg)
        return super(l10n_es_aeat_mod130_report, self).button_confirm(cr, uid,
                                                        ids, context=context)
