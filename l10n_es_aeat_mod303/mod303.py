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
try:
    from openerp.addons.account.report.report_vat import tax_report
except:
    from openerp.addons.account.report.account_tax_report import tax_report


class L10nEsAeatMod303Report(orm.Model):
    _inherit = "l10n.es.aeat.report"
    _name = "l10n.es.aeat.mod303.report"
    _description = "AEAT 303 Report"

    _columns = {
        'company_partner_id': fields.related(
            'company_id', 'partner_id', type='many2one', relation='res.partner',
            string='Partner', store=True),
        'period': fields.selection(
            [('1T', 'First quarter'), ('2T', 'Second quarter'),
             ('3T', 'Third quarter'), ('4T', 'Fourth quarter'),
             ('01', 'January'), ('02', 'February'), ('03', 'March'),
             ('04', 'April'), ('05', 'May'), ('06', 'June'),
             ('07', 'July'), ('08', 'August'), ('09', 'September'),
             ('10', 'October'), ('11', 'November'), ('12', 'December')],
            'Period', states={'done': [('readonly', True)]}),
        'devolucion_mensual': fields.boolean(
            "Devolución Mensual",
            help="Inscrito en el Registro de Devolución Mensual",
            states={'done': [('readonly', True)]}),
        'complementaria': fields.boolean("Autoliquidación complementaria",
                                         states={'done': [('readonly', True)]}),
        'contact_name': fields.char("Full name", size=40),
        'total_devengado': fields.float("IVA devengado", readonly=True),  # 21
        'total_deducir': fields.float("IVA a deducir", readonly=True),  # 37
        'diferencia': fields.float(
            "Diferencia", readonly=True,
            help="( IVA devengado - IVA deducible )"),  # 38
        'porcentaje_atribuible_estado': fields.float(
            "%",
            help="Los sujetos pasivos que tributen conjuntamente a la "
                 "Administración del Estado y a las Diputaciones Forales "
                 "del País Vasco o a la Comunidad Foral de Navarra, "
                 "consignarán en esta casilla el porcentaje del volumen "
                 "de operaciones en territorio común. Los demás sujetos "
                 "pasivos consignarán en esta casilla el 100%",
            states={'done': [('readonly', True)]}),  # 39
        'atribuible_estado': fields.float("Atribuible a la Administración",
                                          readonly=True),  # 40
        'cuota_compensar': fields.float(
            "Cuotas a compensar",
            help="Cuota a compensar de periodos anteriores",
            states={'done': [('readonly', True)]}),  # 41
        'regularizacion_anual': fields.float(
            "Regularización anual",
            help="En la última autoliquidación del  año (la del período "
                 "4T o mes 12) se hará constar, con el signo que "
                 "corresponda, el resultado de la regularización anual "
                 "conforme disponen las Leyes por las que se aprueban el "
                 "Concierto Económico entre el Estado y la Comunidad "
                 "Autónoma del País Vasco y el Convenio Económico entre "
                 "el Estado y la Comunidad Foral de Navarra.""",
            states={'done': [('readonly', True)]}),  # 45
        'resultado_casilla_46': fields.float(
            "Resultado",
            help="Atribuible a la Administración [40] - Cuotas a compensar "
            "[41] + Regularización anual [45]""", readonly=True),  # 46
        'previus_result': fields.float(
            "A deducir",
            help="Resultado de la anterior o anteriores del mismo "
                 "concepto, ejercicio y periodo",
            states={'done': [('readonly', True)]}),  # 47
        'resultado_liquidacion': fields.float("Resultado liquidación",
                                              readonly=True),  # 48
        'compensar': fields.float("Compensar",
                                  states={'done': [('readonly', True)]}),  # 49
        "devolver": fields.float("Devolver",
                                 states={'done': [('readonly', True)]}),
        "ingresar": fields.float("Ingresar",
                                 states={'done': [('readonly', True)]}),
        'cuenta_devolucion_id': fields.many2one(
            "res.partner.bank", "CCC devolución",
            states={'done': [('readonly', True)]}),
        'cuenta_ingreso_id': fields.many2one(
            "res.partner.bank", "CCC Ingreso",
            states={'done': [('readonly', True)]}),
        'sin_actividad': fields.boolean(
            "Sin actividad", states={'done': [('readonly', True)]}),
    }

    _defaults = {
        'number': '303',
        'porcentaje_atribuible_estado': 100,
        'cuota_compensar': 0,
    }

    def _get_period(self, cr, uid, ids, context=None):
        period_obj = self.pool.get("account.period")
        quarter_dict = {
            "1T": 'first',
            "2T": 'second',
            "3T": 'third',
            "4T": 'fourth',
        }
        account_period_id = []
        for mod303 in self.browse(cr, uid, ids, context=context):
            fecha_ini = False
            fecha_fin = False
            dec_year = mod303.fiscalyear_id.date_start.split('-')[0]
            mod = mod303.period
            if mod >= '01' and mod <= '12':
                fecha_ini = datetime.strptime('%s-%s-01'
                                              % (dec_year, mod), '%Y-%m-%d')
                fecha_fin = fecha_ini + relativedelta(months=+1, days=-1)
                account_period_id = period_obj.search(
                    cr, uid,
                    [('date_start', '=', fecha_ini),
                     ('date_stop', '=', fecha_fin)],
                    context=context)
            elif mod in ('1T', '2T', '3T', '4T'):
                month = ((int(mod[0]) - 1) * 3) + 1
                fecha_ini = datetime.strptime('%s-%s-01'
                                              % (dec_year, month), '%Y-%m-%d')
                fecha_fin = fecha_ini + relativedelta(months=3, days=-1)
                account_period_id = period_obj.search(
                    cr, uid,
                    [('date_start', '=', fecha_ini),
                     ('date_stop', '=', fecha_fin)],
                    context=context)
                if not account_period_id:
                    account_period_id = period_obj.search(
                        cr, uid, [('quarter', '=', quarter_dict[mod])],
                        context=context)
            if not account_period_id:
                raise orm.except_orm(
                    _('El periodo seleccionado no coincide con los periodos del'
                      ' ejercicio fiscal: '),
                    dec_year)
        return account_period_id

    def _get_report_lines(self, cr, uid, ids, context=None):
        if isinstance(ids, list):
            id = ids[0]
        else:
            id = ids
        dict_code_values = {}
        for i in range(1, 51):
            dict_code_values["[%.2d]" % i] = 0
        mod303 = self.browse(cr, uid, id, context=context)
        generated_report = tax_report(cr, uid, "account.vat.declaration")
        generated_report.period_ids = self._get_period(cr, uid, [mod303.id],
                                                       context=context)
        generated_report.display_detail = False
        try:
            lines = generated_report._get_lines('invoices',
                                                company_id=mod303.company_id.id)
        except TypeError:
            # Este error ocurre en la rama OCB, ya que se ha añadido en la
            # revisión 9599 un nuevo parámetro posicional al método.
            # Publicado como bug #1269965, pendiente de resolución, esto
            # es un parche temporal
            lines = generated_report._get_lines('invoices', False,
                                                company_id=mod303.company_id.id)
        ordered_lines = sorted(lines, key=lambda k: k['code'])
        for code in dict_code_values.keys():
            for line in ordered_lines:
                if code == line["code"]:
                    dict_code_values[code] += line["tax_amount"]
        return dict_code_values

    def calculate(self, cr, uid, ids, context=None):
        for mod303 in self.browse(cr, uid, ids, context=context):
            report_lines = self._get_report_lines(cr, uid, mod303.id,
                                                  context=context)
            regularizacion_anual = (mod303.regularizacion_anual if
                                    (mod303.period == "4T" or
                                     mod303.period == "12") else 0)
            total_devengado = report_lines.get("[21]")
            total_deducir = report_lines.get("[37]")
            atribuible_estado = ((total_devengado - total_deducir) *
                                 mod303.porcentaje_atribuible_estado / 100)
            casilla_46 = (atribuible_estado - mod303.cuota_compensar +
                          regularizacion_anual)
            previus_result = (mod303.previus_result if mod303.complementaria
                              else 0)
            resultado_liquidacion = casilla_46 - previus_result
            vals = {
                'total_devengado': total_devengado,
                'total_deducir': total_deducir,
                'diferencia': total_devengado - total_deducir,
                'atribuible_estado': atribuible_estado,
                'resultado_casilla_46': casilla_46,
                'resultado_liquidacion': resultado_liquidacion,
                'compensar': (abs(resultado_liquidacion) if
                              resultado_liquidacion < 0
                              and mod303.devolver == 0
                              else 0),
                'ingresar': (resultado_liquidacion if resultado_liquidacion > 0
                             else 0)
            }
            if (mod303.regularizacion_anual > 0 and not
               (mod303.period == "4T" and mod303.period == "12")):
                self.log(
                    cr, uid, mod303.id,
                    _("El valor añadido para la regularizacion anual no se ha "
                      "tenido en cuenta por no ser un periodo de cierre (12 o "
                      "4T)"), context=context)
            self.write(cr, uid, mod303.id, vals, context=context)
        return True

    def button_confirm(self, cr, uid, ids, context=None):
        """Check its records"""
        msg = ""
        for mod303 in self.browse(cr, uid, ids, context=context):
            if mod303.ingresar > 0 and not mod303.cuenta_ingreso_id:
                msg = _('Seleccione una cuenta para ingresar el importe')
            if mod303.devolver > 0 and not mod303.cuenta_devolucion_id:
                msg = _('Seleccione una cuenta para realizar la devolución')
            if mod303.resultado_liquidacion == 0 and not mod303.sin_actividad:
                msg = _("No hay actividad en el periodo seleccionado. "
                        "Marque la casilla correspondinte")
        if msg:
            raise orm.except_orm("", msg)
        return super(L10nEsAeatMod303Report, self).button_confirm(
            cr, uid, ids, context=context)
