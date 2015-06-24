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
from openerp import models, fields, api, exceptions, _
try:
    from openerp.addons.account.report.report_vat import tax_report
except:
    from openerp.addons.account.report.account_tax_report import tax_report


class L10nEsAeatMod303Report(models.Model):
    _inherit = "l10n.es.aeat.report"
    _name = "l10n.es.aeat.mod303.report"
    _description = "AEAT 303 Report"

    def _get_export_conf(self):
        return self.env.ref('l10n_es_aeat_mod303.aeat_mod303_main_export_'
                            'config').id

    number = fields.Char(default='303')
    export_config = fields.Many2one(default=_get_export_conf)
    company_partner_id = fields.Many2one('res.partner', string='Partner',
                                         relation='company_id.partner_id',
                                         store=True)
    period = fields.Many2one("account.period", string='Period',
                             states={'done': [('readonly', True)]})
    devolucion_mensual = fields.Boolean(
        string="Devolución Mensual", states={'done': [('readonly', True)]},
        help="Inscrito en el Registro de Devolución Mensual")
    complementaria = fields.Boolean(string="Autoliquidación complementaria",
                                    states={'done': [('readonly', True)]})
    contact_name = fields.Char(string="Full name", size=40)
    total_devengado = fields.Float(string="IVA devengado", readonly=True)  # 21
    total_deducir = fields.Float(string="IVA a deducir", readonly=True)  # 37
    diferencia = fields.Float(string="Diferencia", readonly=True,
                              help="( IVA devengado - IVA deducible )")  # 38
    porcentaje_atribuible_estado = fields.Float(
        string="%", states={'done': [('readonly', True)]},
        help="Los sujetos pasivos que tributen conjuntamente a la "
        "Administración del Estado y a las Diputaciones Forales "
        "del País Vasco o a la Comunidad Foral de Navarra, "
        "consignarán en esta casilla el porcentaje del volumen "
        "de operaciones en territorio común. Los demás sujetos "
        "pasivos consignarán en esta casilla el 100%", default=100)  # 39
    atribuible_estado = fields.Float(string="Atribuible a la Administración",
                                     readonly=True)  # 40
    cuota_compensar = fields.Float(
        string="Cuotas a compensar", states={'done': [('readonly', True)]},
        help="Cuota a compensar de periodos anteriores", default=0)  # 41
    regularizacion_anual = fields.Float(
        string="Regularización anual",
        states={'done': [('readonly', True)]},
        help="En la última autoliquidación del "
        "año (la del período 4T o mes 12) se hará constar, con el signo "
        "que corresponda, el resultado de la regularización anual "
        "conforme disponen las Leyes por las que se aprueban el "
        "Concierto Económico entre el Estado y la Comunidad Autónoma "
        "del País Vasco y el Convenio Económico entre el Estado y la "
        "Comunidad Foral de Navarra.""")  # 45
    resultado_casilla_46 = fields.Float(
        string="Resultado", readonly=True,
        help="Atribuible a la Administración [40] - Cuotas "
        "a compensar [41] + Regularización anual [45]""")  # 46
    previus_result = fields.Float(
        string="A deducir", help="Resultado de la anterior o anteriores del "
        "mismo concepto, ejercicio y periodo",
        states={'done': [('readonly', True)]})  # 47
    resultado_liquidacion = fields.Float(string="Resultado liquidación",
                                         readonly=True)  # 48
    compensar = fields.Float(string="Compensar",
                             states={'done': [('readonly', True)]})  # 49
    devolver = fields.Float(string="Devolver",
                            states={'done': [('readonly', True)]})
    ingresar = fields.Float(string="Ingresar",
                            states={'done': [('readonly', True)]})
    cuenta_devolucion_id = fields.Many2one(
        "res.partner.bank", string="CCC devolución",
        states={'done': [('readonly', True)]})
    cuenta_ingreso_id = fields.Many2one(
        "res.partner.bank", string="CCC Ingreso",
        states={'done': [('readonly', True)]})
    sin_actividad = fields.Boolean(string="Sin actividad",
                                   states={'done': [('readonly', True)]})
    mod303_lines = fields.One2many('l10n.es.aeat.mod303.report.line',
                                   'mod303_id', string="Lines")

    def __init__(self, pool, cr):
        self._aeat_number = '303'
        super(L10nEsAeatMod303Report, self).__init__(pool, cr)

    @api.multi
    def _get_report_lines(self):
        self.ensure_one()
        dict_code_values = {}
        generated_report = tax_report(self.env.cr, self.env.uid,
                                      "account.vat.declaration",
                                      self.env.context)
        generated_report.period_ids = [self.period.id]
        generated_report.display_detail = False
        lines = generated_report._get_lines('invoices',
                                            company_id=self.company_id.id)
        ordered_lines = sorted(lines, key=lambda k: k['code'])
        for line in ordered_lines:
            if line.get("code", False):
                if not dict_code_values.get(line['code'], False):
                    dict_code_values.update({line["code"]: line["tax_amount"]})
                else:
                    dict_code_values[line["code"]] += line["tax_amount"]
        return dict_code_values

    @api.multi
    def calculate(self):
        account_period_obj = self.env['account.period']
        map_obj = self.env['aeat.mod.map.tax.code']
        line303_obj = self.env['l10n.es.aeat.mod303.report.line']
        for mod303 in self:
            self.mod303_lines.unlink()
            report_lines = mod303._get_report_lines()
            last_period = account_period_obj.search(
                [('fiscalyear_id', '=', mod303.fiscalyear_id.id),
                 ('special', '=', False)], order='date_start')[:-1]
            regularizacion_anual = (mod303.regularizacion_anual if
                                    (mod303.period == last_period) else 0)
            map_lst = map_obj.search(
                [('model', '=', mod303.number),
                 '|', ('date_from', '<=', mod303.period.date_start),
                 ('date_from', '=', False), '|',
                 ('date_to', '>=', mod303.period.date_stop),
                 ('date_to', '=', False)], limit=1)
            for line in map_lst.map_lines:
                val_303_line = {
                    'field_number': line.field_number,
                    'tax_code_amount': report_lines.get(line.tax_code.code,
                                                        0.0),
                    'map_line_id': line.id,
                    'mod303_id': mod303.id}
                line303_obj.create(val_303_line)
            total_devengado = report_lines.get("[21]", 0.0)
            total_deducir = report_lines.get("[23]", 0.0)
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
                              resultado_liquidacion < 0 and
                              mod303.devolver == 0 else 0),
                'ingresar': resultado_liquidacion,
            }
            if (mod303.regularizacion_anual > 0 and
                    mod303.period != last_period):
                mod303.log(_("El valor añadido para la regularizacion anual "
                             "no se ha tenido en cuenta por no ser un periodo "
                             "de cierre (12 o 4T)"))
            mod303.write(vals)
        return True

    @api.multi
    def button_confirm(self):
        """Check its records"""
        msg = ""
        for mod303 in self:
            if mod303.ingresar > 0 and not mod303.cuenta_ingreso_id:
                msg = _('Seleccione una cuenta para ingresar el importe')
            if mod303.devolver > 0 and not mod303.cuenta_devolucion_id:
                msg = _('Seleccione una cuenta para realizar la devolución')
            if mod303.resultado_liquidacion == 0 and not mod303.sin_actividad:
                msg = _("No hay actividad en el periodo seleccionado. "
                        "Marque la casilla correspondinte")
        if msg:
            raise exceptions.Warning(msg)
        return super(L10nEsAeatMod303Report, self).button_confirm()


class L10nEsAeatMod303ReportLine(models.Model):
    _name = "l10n.es.aeat.mod303.report.line"
    _description = "AEAT 303 Report Line"

    field_number = fields.Integer(string="Field number")
    tax_code_amount = fields.Float(string="Tax code amount")
    map_line_id = fields.Many2one('mod303.map.tax.code.line')
    mod303_id = fields.Many2one('l10n.es.aeat.mod303.report')
