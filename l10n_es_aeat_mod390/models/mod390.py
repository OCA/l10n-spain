# -*- coding: utf-8 -*-
# Copyright 2017 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

from openerp import _, api, fields, exceptions, models


REQUIRED_ON_CALCULATED = {
    'calculated': [('required', 'True'), ('readonly', 'False')]
}
EDITABLE_ON_CALCULATED = {
    'calculated': [('readonly', 'False')]
}
ACTIVITY_CODE_SELECTION = [
    ("1",
     u"1: Actividades sujetas al Impuesto sobre Actividades Económicas "
     u"(Activ. Empresariales)"),
    ("2",
     u"2: Actividades sujetas al Impuesto sobre Actividades Económicas "
     u"(Activ. Profesionales y Artísticas)"),
    ("3", u"3: Arrendadores de Locales de Negocios y garajes"),
    ("4",
     u"4: Actividades Agrícolas, Ganaderas o Pesqueras, no sujetas al IAE"),
    ("5",
     u"5: Sujetos pasivos que no hayan iniciado la realización de entregas de "
     u"bienes o prestaciones de servicios correspondientes a actividades "
     u"empresariales o profesionales y no estén dados de alta en el IAE"),
    ("6", u"6: Otras actividades no sujetas al IAE"),
]
REPRESENTATIVE_HELP = _(u"Nombre y apellidos del representante")
NOTARY_CODE_HELP = _(
    u"Código de la notaría en la que se concedió el poder de representación "
    u"para esta persona."
)


class L10nEsAeatMod390Report(models.Model):
    _description = 'AEAT 390 report'
    _inherit = 'l10n.es.aeat.report.tax.mapping'
    _name = 'l10n.es.aeat.mod390.report'
    _aeat_number = '390'
    _period_quarterly = False
    _period_monthly = False
    _period_yearly = True

    # 3. Datos estadísticos
    has_347 = fields.Boolean(
        string=u"¿Obligación del 347?", default=True,
        help=u"Marque la casilla si el sujeto pasivo ha efectuado con alguna "
             u"persona o entidad operaciones por las que tenga obligación de "
             u"presentar la declaración anual de operaciones con terceras "
             u"personas (modelo 347).",
    )
    main_activity = fields.Char(
        string=u"Actividad principal", readonly=True, size=40,
        states=REQUIRED_ON_CALCULATED,
    )
    main_activity_code = fields.Selection(
        selection=ACTIVITY_CODE_SELECTION, states=REQUIRED_ON_CALCULATED,
        string=u"Código actividad principal", readonly=True,
    )
    main_activity_iae = fields.Char(
        string=u"Epígrafe I.A.E. actividad principal", readonly=True, size=4,
        states=REQUIRED_ON_CALCULATED,
    )
    other_first_activity = fields.Char(
        string=u"1ª actividad", readonly=True, size=40,
        states=EDITABLE_ON_CALCULATED,
    )
    other_first_activity_code = fields.Selection(
        selection=ACTIVITY_CODE_SELECTION, states=EDITABLE_ON_CALCULATED,
        string=u"Código 1ª actividad", readonly=True,
    )
    other_first_activity_iae = fields.Char(
        string=u"Epígrafe I.A.E. 1ª actividad", readonly=True, size=4,
        states=EDITABLE_ON_CALCULATED,
    )
    other_second_activity = fields.Char(
        string=u"2ª actividad", readonly=True, size=40,
        states=EDITABLE_ON_CALCULATED,
    )
    other_second_activity_code = fields.Selection(
        selection=ACTIVITY_CODE_SELECTION, states=EDITABLE_ON_CALCULATED,
        string=u"Código 2ª actividad", readonly=True,
    )
    other_second_activity_iae = fields.Char(
        string=u"Epígrafe I.A.E. 2ª actividad", readonly=True, size=4,
        states=EDITABLE_ON_CALCULATED,
    )
    other_third_activity = fields.Char(
        string=u"3ª actividad", readonly=True, size=40,
        states=EDITABLE_ON_CALCULATED,
    )
    other_third_activity_code = fields.Selection(
        selection=ACTIVITY_CODE_SELECTION, states=EDITABLE_ON_CALCULATED,
        string=u"Código 3ª actividad", readonly=True,
    )
    other_third_activity_iae = fields.Char(
        string=u"Epígrafe I.A.E. 3ª actividad", readonly=True, size=4,
        states=EDITABLE_ON_CALCULATED,
    )
    other_fourth_activity = fields.Char(
        string=u"4ª actividad", readonly=True, size=40,
        states=EDITABLE_ON_CALCULATED,
    )
    other_fourth_activity_code = fields.Selection(
        selection=ACTIVITY_CODE_SELECTION, states=EDITABLE_ON_CALCULATED,
        string=u"Código 4ª actividad", readonly=True,
    )
    other_fourth_activity_iae = fields.Char(
        string=u"Epígrafe I.A.E. 4ª actividad", readonly=True, size=4,
        states=EDITABLE_ON_CALCULATED,
    )
    other_fifth_activity = fields.Char(
        string=u"5ª actividad", readonly=True, size=40,
        states=EDITABLE_ON_CALCULATED,
    )
    other_fifth_activity_code = fields.Selection(
        selection=ACTIVITY_CODE_SELECTION, states=EDITABLE_ON_CALCULATED,
        string=u"Código 5ª actividad", readonly=True,
    )
    other_fifth_activity_iae = fields.Char(
        string=u"Epígrafe I.A.E. 5ª actividad", readonly=True, size=4,
        states=EDITABLE_ON_CALCULATED,
    )
    # 4. Representantes
    first_representative_name = fields.Char(
        string=u"Nombre del primer representante", readonly=True, size=80,
        states=REQUIRED_ON_CALCULATED, help=REPRESENTATIVE_HELP,
    )
    first_representative_vat = fields.Char(
        string=u"NIF del primer representante", readonly=True, size=9,
        states=REQUIRED_ON_CALCULATED,
    )
    first_representative_date = fields.Date(
        string=u"Fecha poder del primer representante", readonly=True,
        states=REQUIRED_ON_CALCULATED,
    )
    first_representative_notary = fields.Char(
        string=u"Notaría del primer representante", readonly=True, size=12,
        states=REQUIRED_ON_CALCULATED, help=NOTARY_CODE_HELP,
    )
    second_representative_name = fields.Char(
        string=u"Nombre del segundo representante", readonly=True, size=80,
        states=EDITABLE_ON_CALCULATED, help=REPRESENTATIVE_HELP,
    )
    second_representative_vat = fields.Char(
        string=u"NIF del segundo representante", readonly=True, size=9,
        states=EDITABLE_ON_CALCULATED,
    )
    second_representative_date = fields.Date(
        string=u"Fecha poder del segundo representante", readonly=True,
        states=EDITABLE_ON_CALCULATED,
    )
    second_representative_notary = fields.Char(
        string=u"Notaría del segundo representante", readonly=True, size=12,
        states=EDITABLE_ON_CALCULATED, help=NOTARY_CODE_HELP,
    )
    third_representative_name = fields.Char(
        string=u"Nombre del tercer representante", readonly=True, size=80,
        states=EDITABLE_ON_CALCULATED, help=REPRESENTATIVE_HELP,
    )
    third_representative_vat = fields.Char(
        string=u"NIF del tercer representante", readonly=True, size=9,
        states=EDITABLE_ON_CALCULATED,
    )
    third_representative_date = fields.Date(
        string=u"Fecha poder del tercer representante", readonly=True,
        states=EDITABLE_ON_CALCULATED,
    )
    third_representative_notary = fields.Char(
        string=u"Notaría del tercer representante", readonly=True, size=12,
        states=EDITABLE_ON_CALCULATED, help=NOTARY_CODE_HELP,
    )
    # 5. Régimen general
    casilla_33 = fields.Float(
        compute="_compute_casilla_33", string=u"[33] Total bases IVA",
        store=True,
    )
    casilla_34 = fields.Float(
        compute="_compute_casilla_34", string=u"[34] Total cuotas IVA",
        store=True,
    )
    casilla_47 = fields.Float(
        compute="_compute_casilla_47", store=True,
        string=u"[47] Total cuotas IVA y recargo de equivalencia",
    )
    casilla_48 = fields.Float(
        compute="_compute_casilla_48", store=True,
        string=u"[48] Total base deducible operaciones corrientes",
    )
    casilla_49 = fields.Float(
        compute="_compute_casilla_49", store=True,
        string=u"[49] Total cuota deducible operaciones corrientes",
    )
    casilla_52 = fields.Float(
        compute="_compute_casilla_52", store=True,
        string=u"[52] Total base deducible importaciones corrientes",
    )
    casilla_53 = fields.Float(
        compute="_compute_casilla_53", store=True,
        string=u"[53] Total cuota deducible importaciones corrientes",
    )
    casilla_56 = fields.Float(
        compute="_compute_casilla_56", store=True,
        string=u"[56] Total base deducible adq. intracomunitarias bienes",
    )
    casilla_57 = fields.Float(
        compute="_compute_casilla_57", store=True,
        string=u"[57] Total cuota deducible adq. intracomunitarias bienes",
    )
    casilla_597 = fields.Float(
        compute="_compute_casilla_597", store=True,
        string=u"[597] Total base deducible adq. intracomunitarias servicios",
    )
    casilla_598 = fields.Float(
        compute="_compute_casilla_598", store=True,
        string=u"[598] Total cuota deducible adq. intracomunitarias servicios",
    )
    casilla_64 = fields.Float(
        compute="_compute_casilla_64", store=True,
        string=u"[64] Suma de deducciones",
    )
    casilla_65 = fields.Float(
        compute="_compute_casilla_65", store=True,
        string=u"[65] Result. rég. gral.",
    )
    casilla_85 = fields.Float(
        string=u"[85] Compens. ejercicio anterior", readonly=True,
        states=EDITABLE_ON_CALCULATED,
        help=u"Si en la autoliquidación del último período del ejercicio "
             u"anterior resultó un saldo a su favor y usted optó por la "
             u"compensación, consigne en esta casilla la cantidad a "
             u"compensar, salvo que la misma haya sido modificada por la "
             u"Administración, en cuyo caso se consignará esta última.",
    )
    casilla_86 = fields.Float(
        compute="_compute_casilla_86", store=True,
        string=u"[86] Result. liquidación",
    )
    # 9. Resultado de las liquidaciones
    casilla_95 = fields.Float(
        string=u"[95] Total resultados a ingresar modelo 303",
        help=u"Se consignará la suma de las cantidades a ingresar por el "
             u"Impuesto como resultado de las autoliquidaciones periódicas "
             u"del ejercicio que no tributen en el régimen especial del grupo "
             u"de entidades, incluyendo aquellas para las que se hubiese "
             u"solicitado aplazamiento, fraccionamiento o no se hubiese "
             u"efectuado el pago.",
        states=REQUIRED_ON_CALCULATED, readonly=True,
    )
    casilla_97 = fields.Float(
        string=u"[97] Result. 303 último periodo a compensar",
        help=u"Si el resultado de la última autoliquidación fue a compensar, "
             u"consignará en esta casilla el importe de la misma.",
        states=REQUIRED_ON_CALCULATED, readonly=True,
    )
    casilla_98 = fields.Float(
        string=u"[98] Result. 303 último periodo a devolver",
        help=u"Si el resultado de la última autoliquidación fue a devolver, "
             u"consignará en esta casilla el importe de la misma.",
        states=REQUIRED_ON_CALCULATED, readonly=True,
    )
    casilla_108 = fields.Float(
        string=u"[108] Total vol. oper.",
        compute="_compute_casilla_108", store=True,
    )

    @api.multi
    @api.depends('tax_line_ids')
    def _compute_casilla_33(self):
        for report in self:
            report.casilla_33 = sum(report.tax_line_ids.filtered(
                lambda x: x.field_number in (
                    1, 3, 5,  # Régimen ordinario
                    500, 502, 504,  # Intragrupo - no incluido aún
                    643, 645, 647,  # Criterio de caja - no incluido aún
                    7, 9, 11,  # Bienes usados, etc - no incluido aún
                    13,  # Agencias de viajes - no incluido aún
                    21, 23, 25,  # Adquis. intracomunitaria bienes
                    545, 547, 551,  # Adquis. intracomunitaria servicios
                    27,  # IVA otras operaciones sujeto pasivo
                    29,  # Modificación bases y cuotas
                    649,  # Modif. bases y cuotas intragrupo - no incluido aún
                    31,  # Modif. bases y cuotas concurso ac. - no incluido aún
                )
            ).mapped('amount'))

    @api.multi
    @api.depends('tax_line_ids')
    def _compute_casilla_34(self):
        for report in self:
            report.casilla_34 = sum(report.tax_line_ids.filtered(
                lambda x: x.field_number in (
                    2, 4, 6,  # Régimen ordinario
                    501, 503, 505,  # Intragrupo - no incluido aún
                    644, 646, 648,  # Criterio de caja - no incluido aún
                    8, 10, 12,  # Bienes usados, etc - no incluido aún
                    14,  # Agencias de viajes - no incluido aún
                    22, 24, 26,  # Adquis. intracomunitaria bienes
                    546, 548, 552,  # Adquis. intracomunitaria servicios
                    28,  # IVA otras operaciones sujeto pasivo
                    30,  # Modificación bases y cuotas
                    650,  # Modif. bases y cuotas intragrupo - no incluido aún
                    32,  # Modif. bases y cuotas concurso ac. - no incluido aún
                )
            ).mapped('amount'))

    @api.multi
    @api.depends('casilla_34', 'tax_line_ids')
    def _compute_casilla_47(self):
        for report in self:
            report.casilla_47 = (
                report.casilla_34 +
                sum(report.tax_line_ids.filtered(
                    lambda x: x.field_number in (
                        36, 600, 602,  # Recargo de equivalencia
                        44,  # Modificación recargo de equivalencia
                        46,  # Mod. recargo equiv. concurso - no incluido aún
                    )
                ).mapped('amount'))
            )

    @api.multi
    @api.depends('tax_line_ids')
    def _compute_casilla_38(self):
        for report in self:
            report.casilla_38 = sum(report.tax_line_ids.filtered(
                lambda x: x.field_number in (
                    190, 192, 555, 603, 194, 557, 605,
                )
            ).mapped('amount'))

    @api.multi
    @api.depends('tax_line_ids')
    def _compute_casilla_39(self):
        for report in self:
            report.casilla_39 = sum(report.tax_line_ids.filtered(
                lambda x: x.field_number in (
                    191, 193, 556, 604, 195, 558, 606,
                )
            ).mapped('amount'))

    @api.multi
    @api.depends('tax_line_ids')
    def _compute_casilla_48(self):
        for report in self:
            report.casilla_48 = sum(report.tax_line_ids.filtered(
                lambda x: x.field_number in (
                    190, 192, 555, 603, 194, 557, 605,
                )
            ).mapped('amount'))

    @api.multi
    @api.depends('tax_line_ids')
    def _compute_casilla_49(self):
        for report in self:
            report.casilla_49 = sum(report.tax_line_ids.filtered(
                lambda x: x.field_number in (
                    191, 193, 556, 604, 195, 558, 606,
                )
            ).mapped('amount'))

    @api.multi
    @api.depends('tax_line_ids')
    def _compute_casilla_52(self):
        for report in self:
            report.casilla_52 = sum(report.tax_line_ids.filtered(
                lambda x: x.field_number in (
                    202, 204, 571, 619, 206, 573, 621,
                )
            ).mapped('amount'))

    @api.multi
    @api.depends('tax_line_ids')
    def _compute_casilla_53(self):
        for report in self:
            report.casilla_53 = sum(report.tax_line_ids.filtered(
                lambda x: x.field_number in (
                    203, 205, 572, 620, 207, 574, 622,
                )
            ).mapped('amount'))

    @api.multi
    @api.depends('tax_line_ids')
    def _compute_casilla_56(self):
        for report in self:
            report.casilla_56 = sum(report.tax_line_ids.filtered(
                lambda x: x.field_number in (
                    214, 216, 579, 627, 218, 581, 629,
                )
            ).mapped('amount'))

    @api.multi
    @api.depends('tax_line_ids')
    def _compute_casilla_57(self):
        for report in self:
            report.casilla_57 = sum(report.tax_line_ids.filtered(
                lambda x: x.field_number in (
                    215, 217, 580, 628, 219, 582, 630,
                )
            ).mapped('amount'))

    @api.multi
    @api.depends('tax_line_ids')
    def _compute_casilla_597(self):
        for report in self:
            report.casilla_597 = sum(report.tax_line_ids.filtered(
                lambda x: x.field_number in (
                    587, 589, 591, 635, 593, 595, 637,
                )
            ).mapped('amount'))

    @api.multi
    @api.depends('tax_line_ids')
    def _compute_casilla_598(self):
        for report in self:
            report.casilla_598 = sum(report.tax_line_ids.filtered(
                lambda x: x.field_number in (
                    588, 590, 592, 636, 594, 596, 638,
                )
            ).mapped('amount'))

    @api.multi
    @api.depends('casilla_49', 'casilla_53', 'casilla_57', 'casilla_598',
                 'tax_line_ids')
    def _compute_casilla_64(self):
        for report in self:
            report.casilla_64 = (
                report.casilla_49 + report.casilla_53 +
                report.casilla_57 + report.casilla_598 +
                sum(report.tax_line_ids.filtered(
                    lambda x: x.field_number == 62
                ).mapped('amount'))
            )

    @api.multi
    @api.depends('casilla_47', 'casilla_64')
    def _compute_casilla_65(self):
        for report in self:
            report.casilla_65 = report.casilla_47 - report.casilla_64

    @api.multi
    @api.depends('casilla_65', 'casilla_85')
    def _compute_casilla_86(self):
        for report in self:
            # It takes 65 instead of 84 + 659 as the rest are 0
            report.casilla_86 = report.casilla_65 - report.casilla_85

    @api.multi
    @api.depends('tax_line_ids')
    def _compute_casilla_108(self):
        for report in self:
            report.casilla_108 = sum(
                report.tax_line_ids.filtered(
                    lambda x: x.field_number in (
                        99, 653, 103, 104, 105, 110, 112, 100, 101, 102, 227,
                        228,
                    )
                ).mapped('amount')
            ) - sum(
                report.tax_line_ids.filtered(
                    lambda x: x.field_number in (
                        106, 107,
                    )
                ).mapped('amount')
            )

    @api.multi
    @api.constrains('type')
    def _check_type(self):
        if 'C' in self.mapped('type'):
            raise exceptions.UserError(
                _("You cannot make complementary reports for this model.")
            )
