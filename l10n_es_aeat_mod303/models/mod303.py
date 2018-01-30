# -*- coding: utf-8 -*-
# © 2013 - Guadaltech - Alberto Martín Cortada
# © 2015 - AvanzOSC - Ainara Galdona
# © 2014-2016 - Serv. Tecnol. Avanzados - Pedro M. Baeza
# © 2018 - Otherway Creatives - Pedro Rodriguez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api, _


class L10nEsAeatMod303Report(models.Model):
    _inherit = "l10n.es.aeat.report.tax.mapping"
    _name = "l10n.es.aeat.mod303.report"
    _description = "AEAT 303 Report"

    def _get_export_conf(self):
        try:
            return self.env.ref(
                'l10n_es_aeat_mod303.'
                'aeat_mod303_2017_main_export_config').id
        except ValueError:
            return self.env['aeat.model.export.config']

    def _default_counterpart_303(self):
        return self.env['account.account'].search(
            [('code', 'like', '4750%'), ('type', '!=', 'view')])[:1]

    @api.multi
    @api.depends('tax_lines', 'tax_lines.amount')
    def _compute_total_devengado(self):
        casillas_devengado = (3, 6, 9, 11, 13, 15, 18, 21, 24, 26)
        for report in self:
            tax_lines = report.tax_lines.filtered(
                lambda x: x.field_number in casillas_devengado)
            report.total_devengado = sum(tax_lines.mapped('amount'))

    @api.multi
    @api.depends('tax_lines', 'tax_lines.amount')
    def _compute_total_deducir(self):
        casillas_deducir = (29, 31, 33, 35, 37, 39, 41, 42, 43, 44)
        for report in self:
            tax_lines = report.tax_lines.filtered(
                lambda x: x.field_number in casillas_deducir)
            report.total_deducir = sum(tax_lines.mapped('amount'))

    @api.multi
    @api.depends('total_devengado', 'total_deducir')
    def _compute_casilla_46(self):
        for report in self:
            report.casilla_46 = (report.total_devengado -
                                 report.total_deducir)

    @api.multi
    @api.depends('porcentaje_atribuible_estado', 'casilla_46')
    def _compute_atribuible_estado(self):
        for report in self:
            report.atribuible_estado = (
                report.casilla_46 *
                report.porcentaje_atribuible_estado / 100)

    @api.multi
    @api.depends('atribuible_estado', 'cuota_compensar',
                 'regularizacion_anual', 'casilla_77')
    def _compute_casilla_69(self):
        for report in self:
            report.casilla_69 = (
                report.atribuible_estado + report.casilla_77 +
                report.cuota_compensar + report.regularizacion_anual)

    @api.multi
    @api.depends('casilla_88', 'exonerated_390')
    def _compute_exonerated_390_val(self):
        for report in self:
            report.exonerated_390_val = 0
            if (report.period_type in ('4T', '12') and
                    report.exonerated_390):
                if report.casilla_88 != 0.:
                    report.exonerated_390_val = 1
                else:
                    report.exonerated_390_val = 2

    @api.multi
    @api.depends('clave_B_quarters', 'clave_B_months')
    def _compute_clave_B(self):
        for report in self:
            report.clave_B = ''
            if report.period_type == '4T':
                report.clave_B = report.clave_B_quarters
            elif report.period_type == '12':
                report.clave_B = report.clave_B_months

    @api.multi
    @api.depends('tax_lines', 'exonerated_390')
    def _compute_casilla_80(self):
        casillas_base_devengado = (1, 4, 7)
        casillas_base_modif = (14,)
        for report in self:
            if not report.exonerated_390:
                report.casilla_80 = 0
                continue
            tax_lines_devengado = report.tax_lines.filtered(
                lambda x: x.field_number in casillas_base_devengado)
            tax_lines_modif = report.tax_lines.filtered(
                lambda x: x.field_number in casillas_base_modif)
            if not (tax_lines_devengado or tax_lines_modif):
                report.casilla_80 = 0
                continue
            codes_devengado = []
            for tax_line in tax_lines_devengado:
                codes_devengado += tax_line.map_line.\
                    mapped('tax_codes.code')
            codes_modif = []
            for tax_line in tax_lines_modif:
                codes_modif += tax_line.map_line.\
                    mapped('tax_codes.code')
            move_lines_devengado = (report._get_tax_code_lines(
                codes=codes_devengado))
            # Obtenemos las lineas de minoración de bases sin incluir
            # hijos para evitar sumar las deducciones de facturas
            # rectificativas de proveedor con ISP (MBYCRBIISN)
            move_lines_modif = (report._get_tax_code_lines(
                codes=codes_modif, include_children=False))
            report.casilla_80 = (
                sum(move_lines_devengado.mapped('tax_amount')) +
                sum(move_lines_modif.mapped('tax_amount')))

    @api.multi
    @api.depends('tax_lines', 'exonerated_390')
    def _compute_casilla_83(self):
        for report in self:
            if not report.exonerated_390:
                report.casilla_83 = 0
                continue
            codes_devengado = ['OESDAD']
            move_lines_devengado = (report._get_tax_code_lines(
                codes=codes_devengado))
            report.casilla_83 = sum(
                move_lines_devengado.mapped('tax_amount'))

    @api.multi
    @api.depends('tax_lines', 'exonerated_390')
    def _compute_casilla_84(self):
        casillas_base_devengado = (61,)
        for report in self:
            if not report.exonerated_390:
                report.casilla_84 = 0
                continue
            tax_lines_devengado = report.tax_lines.filtered(
                lambda x: x.field_number in casillas_base_devengado)
            codes_devengado = []
            for tax_line in tax_lines_devengado:
                codes_devengado += tax_line.map_line.\
                    mapped('tax_codes.code')
            move_lines_devengado = (report._get_tax_code_lines(
                codes=codes_devengado))
            report.casilla_84 = sum(
                move_lines_devengado.mapped('tax_amount'))

    @api.multi
    @api.depends('tax_lines', 'exonerated_390')
    def _compute_casilla_93(self):
        casillas_base_devengado = (59,)
        for report in self:
            if not report.exonerated_390:
                report.casilla_93 = 0
                continue
            tax_lines_devengado = report.tax_lines.filtered(
                lambda x: x.field_number in casillas_base_devengado)
            if not tax_lines_devengado:
                report.casilla_93 = 0
                continue
            codes_devengado = []
            for tax_line in tax_lines_devengado:
                codes_devengado += tax_line.map_line.\
                    mapped('tax_codes.code')
            move_lines_devengado = (report._get_tax_code_lines(
                codes=codes_devengado))
            report.casilla_93 = sum(
                move_lines_devengado.mapped('tax_amount'))

    @api.multi
    @api.depends('tax_lines', 'exonerated_390')
    def _compute_casilla_94(self):
        for report in self:
            if not report.exonerated_390:
                report.casilla_94 = 0
                continue
            codes_devengado = ['EYOA']
            move_lines_devengado = (report._get_tax_code_lines(
                codes=codes_devengado))
            report.casilla_94 = sum(
                move_lines_devengado.mapped('tax_amount'))

    @api.multi
    @api.depends('tax_lines', 'exonerated_390')
    def _compute_casilla_96(self):
        casillas_base_devengado = (16, 19, 22)
        casillas_base_modif = (25,)
        for report in self:
            if not report.exonerated_390:
                report.casilla_96 = 0
                continue
            tax_lines_devengado = report.tax_lines.filtered(
                lambda x: x.field_number in casillas_base_devengado)
            tax_lines_modif = report.tax_lines.filtered(
                lambda x: x.field_number in casillas_base_modif)
            if not (tax_lines_devengado or tax_lines_modif):
                report.casilla_96 = 0
                continue
            codes_devengado = []
            for tax_line in tax_lines_devengado:
                codes_devengado += tax_line.map_line.\
                    mapped('tax_codes.code')
            codes_modif = []
            for tax_line in tax_lines_modif:
                codes_modif += tax_line.map_line.\
                    mapped('tax_codes.code')
            move_lines_devengado = (report._get_tax_code_lines(
                codes=codes_devengado))
            move_lines_modif = (report._get_tax_code_lines(
                codes=codes_modif))
            report.casilla_96 = (
                sum(move_lines_devengado.mapped('tax_amount')) +
                sum(move_lines_modif.mapped('tax_amount')))

    @api.multi
    @api.depends('casilla_80', 'casilla_83', 'casilla_84', 'casilla_93',
                 'casilla_94', 'casilla_96')
    def _compute_casilla_88(self):
        for report in self:
            if not report.exonerated_390:
                report.casilla_88 = 0
                continue
            report.casilla_88 = (report.casilla_80 + report.casilla_83 +
                                 report.casilla_84 + report.casilla_93 +
                                 report.casilla_94 + report.casilla_96)

    @api.multi
    @api.depends('casilla_69', 'previous_result')
    def _compute_resultado_liquidacion(self):
        for report in self:
            report.resultado_liquidacion = (
                report.casilla_69 - report.previous_result)

    currency_id = fields.Many2one(
        comodel_name='res.currency', string='Currency',
        related='company_id.currency_id', store=True, readonly=True)
    number = fields.Char(default='303')
    export_config = fields.Many2one(default=_get_export_conf)
    company_partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        relation='company_id.partner_id',
        store=True)
    devolucion_mensual = fields.Boolean(
        string="Devolución mensual",
        states={'done': [('readonly', True)]},
        help="Inscrito en el Registro de Devolución Mensual")
    total_devengado = fields.Float(
        string="[27] IVA devengado", readonly=True,
        compute="_compute_total_devengado", store=True)
    total_deducir = fields.Float(
        string="[45] IVA a deducir", readonly=True,
        compute="_compute_total_deducir", store=True)
    casilla_46 = fields.Float(
        string="[46] Resultado régimen general", readonly=True,
        store=True,
        help="(IVA devengado - IVA deducible)",
        compute="_compute_casilla_46")
    porcentaje_atribuible_estado = fields.Float(
        string="[65] % atribuible al Estado",
        states={'done': [('readonly', True)]},
        help="Los sujetos pasivos que tributen conjuntamente a la "
             "Administración del Estado y a las Diputaciones Forales "
             "del País Vasco o a la Comunidad Foral de Navarra, "
             "consignarán en esta casilla el porcentaje del volumen "
             "de operaciones en territorio común. Los demás sujetos "
             "pasivos consignarán en esta casilla el 100%", default=100)
    atribuible_estado = fields.Float(
        string="[66] Atribuible a la Administración", readonly=True,
        compute="_compute_atribuible_estado", store=True)
    cuota_compensar = fields.Float(
        string="[67] Cuotas a compensar", default=0,
        states={'done': [('readonly', True)]},
        help="Cuota a compensar de periodos anteriores, en los que su "
             "declaración fue a devolver y se escogió la opción de "
             "compensación posterior")
    regularizacion_anual = fields.Float(
        string="[68] Regularización anual",
        states={'done': [('readonly', True)]},
        help="En la última autoliquidación del año (la del período 4T "
             "o mes 12) se hará constar, con el signo que corresponda, "
             "el resultado de la regularización anual conforme "
             "disponen las Leyes por las que se aprueban el Concierto "
             "Económico entre el Estado y la Comunidad Autónoma del "
             "País Vasco y el Convenio Económico entre el Estado y la "
             "Comunidad Foral de Navarra.")
    casilla_69 = fields.Float(
        string="[69] Resultado", readonly=True,
        compute="_compute_casilla_69",
        help="Atribuible a la Administración [66] - Cuotas a "
             "compensar [67] + Regularización anual [68]""", store=True)
    casilla_77 = fields.Float(
        string="[77] Iva Diferido (Liquidado por aduana)",
        help="Se hará constar el importe de las cuotas del Impuesto "
             "a la importación incluidas en los documentos en los que "
             "conste la liquidación practicada por la Administración "
             "recibidos en el periodo de liquidación. Solamente podrá "
             "cumplimentarse esta casilla cuando se cumplan los "
             "requisitos establecidos en el artículo 74.1 del "
             "Reglamento del Impuesto sobre el Valor Añadido. ")
    previous_result = fields.Float(
        string="[70] A deducir",
        help="Resultado de la anterior o anteriores declaraciones del "
             "mismo concepto, ejercicio y periodo",
        states={'done': [('readonly', True)]})
    resultado_liquidacion = fields.Float(
        string="[71] Liquidación", readonly=True,
        compute="_compute_resultado_liquidacion", store=True)
    result_type = fields.Selection(
        selection=[('I', 'A ingresar'),
                   ('D', 'A devolver'),
                   ('C', 'A compensar'),
                   ('N', 'Sin actividad/Resultado cero')],
        compute="_compute_result_type", store=True, readonly=False)
    compensate = fields.Boolean(
        string="Compensate", states={'done': [('readonly', True)]},
        help="Si se marca, indicará que el importe a devolver se "
             "compensará en posteriores declaraciones")
    bank_account = fields.Many2one(
        comodel_name="res.partner.bank", string="Bank account",
        states={'done': [('readonly', True)]})
    counterpart_account = fields.Many2one(
        default=_default_counterpart_303)
    allow_posting = fields.Boolean(default=True)
    exonerated_390 = fields.Boolean(
        states={'done': [('readonly', True)]},
        string="Exonerado de presentar el modelo 390",
        help="Si se marca, indicará que la empresa está exonerada de "
             "presentar la Declaración-resumen anual del IVA, modelo "
             "390")
    exonerated_390_val = fields.Integer(
        string="Valor de casilla exonerado 390",
        compute='_compute_exonerated_390_val',
        help="Será 0 para todos los periodos menos el 4T ó 12. En 4T "
             "ó 12 será 0 para los no exonerados; para exonerados será "
             "1 si hay volumen de operaciones y 2 si no hay volumen de "
             "operaciones")
    clave_B = fields.Char(compute='_compute_clave_B',
                          string="B Clave")
    clave_B_quarters = fields.Selection(
        string="Clave de actividad",
        states={'done': [('readonly', True)]},
        selection=[(0, 'Sin epígrafe'),
                   (1, 'Actividades sujetas a I.A.E'),
                   (2, 'Actividades Agrícolas, Ganaderas, Forestales '
                       'o  Pesqueras no sujetas al I.A.E'),
                   (3, 'Arrendadores de bienes inmuebles de naturaleza '
                       'urbana')],
        default=0,
        help="Seleccione en función de la actividad ejercida")
    clave_B_months = fields.Selection(
        string="Clave de actividad",
        states={'done': [('readonly', True)]},
        selection=[(0, 'Sin epígrafe'),
                   (1, 'Actividades sujetas al Impuesto sobre '
                       'Actividades Económicas (Activ. Empresariales)'),
                   (2, 'Actividades sujetas al Impuesto sobre '
                       'Actividades Económicas (Activ. Profesionales y '
                       'Artísticas)'),
                   (3, 'Arrendadores de Locales de Negocios y garajes'),
                   (4, 'Actividades  Agrícolas,  Ganaderas  o  '
                       'Pesqueras,  no  sujetas  al IAE'),
                   (5, 'Sujeto pasivos sin iniciar actividad y no dado '
                       'de alta en IAE'),
                   (6, 'Otras actividades no sujetas al IAE')],
        default=0,
        help="Seleccione en función de la actividad ejercida")
    epigrafe_IAE = fields.Char(
        string='Epígrafe IAE', size=4,
        states={'done': [('readonly', True)]},
        help="Indique, en su caso, el Epígrafe del Impuesto sobre "
             "Actividades Económicas de la actividad desarrollada")
    casilla_80 = fields.Float(
        string="[80] Operaciones en régimen general", readonly=True,
        compute="_compute_casilla_80", store=True,
        help="Volumen de operaciones realizadas en el ejercicio, "
             "excluido el propio IVA y, en su caso, el recargo de "
             "equivalencia, de las entregas de bienes y prestaciones "
             "de servicios en régimen general")
    casilla_83 = fields.Float(
        string="[83] Operaciones exentas sin derecho a deducción",
        readonly=True, compute="_compute_casilla_83", store=True,
        help="Importe de las operaciones realizadas en el ejercicio "
             "exentas sin derecho a deducción, como las mencionadas en "
             "el artículo 20 de la Ley del IVA")
    casilla_84 = fields.Float(
        compute="_compute_casilla_84",
        readonly=True, store=True,
        string="[84] Operaciones no sujetas por reglas de localización "
               "o con ISP",
        help="Importe de las entregas de bienes y prestaciones de "
             "servicios realizadas en el ejercicio no sujetas por "
             "aplicación de las reglas de localización o con inversión "
             "del sujeto pasivo")
    casilla_93 = fields.Float(
        string="[93] Entregas intracomunitatias exentas", readonly=True,
        compute="_compute_casilla_93", store=True,
        help="Importe de las entregas comunitarias realizadas en el "
             "ejercicio exentas en virtud de lo dispuesto en el "
             "artículo 25 de la Ley del IVA")
    casilla_94 = fields.Float(
        compute="_compute_casilla_94",
        readonly=True, store=True,
        string="[94] Exportaciones y otras operaciones exentas con "
               "derecho a deducción",
        help="Importe de las contraprestaciones correspondienete a las "
             "exportaciones y operaciones asimiladas a la exportación "
             "realizadas en el ejercicio")
    casilla_96 = fields.Float(
        compute="_compute_casilla_96",
        string="[96] Operaciones con recargo de equivalencia",
        readonly=True, store=True,
        help="Importe de las entregas de bienes realizadas en el "
             "ejercicio en el ámbito del regimen especial del recargo "
             "de equivalencia")
    casilla_88 = fields.Float(
        string="[88] Total volumen de operaciones",
        compute='_compute_casilla_88', readonly=True, store=True,
        help="Importe total del volumen de operaciones determinado de "
             "acuerdo con el artículo 121 de la Ley del IVA")

    def __init__(self, pool, cr):
        self._aeat_number = '303'
        super(L10nEsAeatMod303Report, self).__init__(pool, cr)

    @api.multi
    def _compute_allow_posting(self):
        for report in self:
            report.allow_posting = True

    @api.multi
    @api.depends('resultado_liquidacion')
    def _compute_result_type(self):
        for report in self:
            if report.resultado_liquidacion == 0:
                report.result_type = 'N'
            elif report.resultado_liquidacion > 0:
                report.result_type = 'I'
            else:
                if report.devolucion_mensual:
                    report.result_type = 'D'
                else:
                    report.result_type = 'C'

    @api.onchange('period_type', 'fiscalyear_id')
    def onchange_period_type(self):
        super(L10nEsAeatMod303Report, self).onchange_period_type()
        if self.period_type not in ('4T', '12'):
            self.regularizacion_anual = 0
            self.exonerated_390 = False
        if (not self.fiscalyear_id or
                self.fiscalyear_id.date_start < '2018-01-01'):
            self.export_config = self.env.ref(
                'l10n_es_aeat_mod303.'
                'aeat_mod303_2017_main_export_config')
        else:
            self.export_config = self.env.ref(
                'l10n_es_aeat_mod303.'
                'aeat_mod303_2018_main_export_config')

    @api.onchange('type')
    def onchange_type(self):
        if self.type != 'C':
            self.previous_result = 0

    @api.onchange('result_type')
    def onchange_result_type(self):
        if self.result_type != 'C':
            self.compensate = False

    @api.onchange('exonerated_390')
    def onchange_exonerated_390(self):
        self.clave_B_quarters = False
        self.clave_B_months = False
        self.epigrafe_IAE = False

    @api.multi
    def button_confirm(self):
        """Check records"""
        msg = ""
        for mod303 in self:
            if mod303.result_type == 'I' and not mod303.bank_account:
                msg = _('Select an account for making the charge')
            if mod303.result_type == 'D' and not mod303.bank_account:
                msg = _('Select an account for receiving the money')
        if msg:
            # Don't raise error, because data is not used
            # raise exceptions.Warning(msg)
            pass
        return super(L10nEsAeatMod303Report, self).button_confirm()
