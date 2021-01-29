# Copyright 2017-2021 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

from odoo import _, api, exceptions, fields, models
from odoo.tools import float_compare

REQUIRED_ON_CALCULATED = {"calculated": [("required", "True"), ("readonly", "False")]}
EDITABLE_ON_CALCULATED = {"calculated": [("readonly", "False")]}
ACTIVITY_CODE_SELECTION = [
    (
        "1",
        "1: Actividades sujetas al Impuesto sobre Actividades Económicas "
        "(Activ. Empresariales)",
    ),
    (
        "2",
        "2: Actividades sujetas al Impuesto sobre Actividades Económicas "
        "(Activ. Profesionales y Artísticas)",
    ),
    ("3", "3: Arrendadores de Locales de Negocios y garajes"),
    ("4", "4: Actividades Agrícolas, Ganaderas o Pesqueras, no sujetas al IAE"),
    (
        "5",
        "5: Sujetos pasivos que no hayan iniciado la realización de entregas "
        "de bienes o prestaciones de servicios correspondientes a actividades "
        "empresariales o profesionales y no estén dados de alta en el IAE",
    ),
    ("6", "6: Otras actividades no sujetas al IAE"),
]
REPRESENTATIVE_HELP = _("Nombre y apellidos del representante")
NOTARY_CODE_HELP = _(
    "Código de la notaría en la que se concedió el poder de representación "
    "para esta persona."
)


class L10nEsAeatMod390Report(models.Model):
    _description = "AEAT 390 report"
    _inherit = "l10n.es.aeat.report.tax.mapping"
    _name = "l10n.es.aeat.mod390.report"
    _aeat_number = "390"
    _period_quarterly = False
    _period_monthly = False
    _period_yearly = True

    # 3. Datos estadísticos
    has_347 = fields.Boolean(
        string="¿Obligación del 347?",
        default=True,
        help="Marque la casilla si el sujeto pasivo ha efectuado con alguna "
        "persona o entidad operaciones por las que tenga obligación de "
        "presentar la declaración anual de operaciones con terceras "
        "personas (modelo 347).",
    )
    main_activity = fields.Char(
        string="Actividad principal",
        readonly=True,
        size=40,
        states=REQUIRED_ON_CALCULATED,
    )
    main_activity_code = fields.Selection(
        selection=ACTIVITY_CODE_SELECTION,
        states=REQUIRED_ON_CALCULATED,
        string="Código actividad principal",
        readonly=True,
    )
    main_activity_iae = fields.Char(
        string="Epígrafe I.A.E. actividad principal",
        readonly=True,
        size=4,
        states=REQUIRED_ON_CALCULATED,
    )
    other_first_activity = fields.Char(
        string="1ª actividad", readonly=True, size=40, states=EDITABLE_ON_CALCULATED,
    )
    other_first_activity_code = fields.Selection(
        selection=ACTIVITY_CODE_SELECTION,
        states=EDITABLE_ON_CALCULATED,
        string="Código 1ª actividad",
        readonly=True,
    )
    other_first_activity_iae = fields.Char(
        string="Epígrafe I.A.E. 1ª actividad",
        readonly=True,
        size=4,
        states=EDITABLE_ON_CALCULATED,
    )
    other_second_activity = fields.Char(
        string="2ª actividad", readonly=True, size=40, states=EDITABLE_ON_CALCULATED,
    )
    other_second_activity_code = fields.Selection(
        selection=ACTIVITY_CODE_SELECTION,
        states=EDITABLE_ON_CALCULATED,
        string="Código 2ª actividad",
        readonly=True,
    )
    other_second_activity_iae = fields.Char(
        string="Epígrafe I.A.E. 2ª actividad",
        readonly=True,
        size=4,
        states=EDITABLE_ON_CALCULATED,
    )
    other_third_activity = fields.Char(
        string="3ª actividad", readonly=True, size=40, states=EDITABLE_ON_CALCULATED,
    )
    other_third_activity_code = fields.Selection(
        selection=ACTIVITY_CODE_SELECTION,
        states=EDITABLE_ON_CALCULATED,
        string="Código 3ª actividad",
        readonly=True,
    )
    other_third_activity_iae = fields.Char(
        string="Epígrafe I.A.E. 3ª actividad",
        readonly=True,
        size=4,
        states=EDITABLE_ON_CALCULATED,
    )
    other_fourth_activity = fields.Char(
        string="4ª actividad", readonly=True, size=40, states=EDITABLE_ON_CALCULATED,
    )
    other_fourth_activity_code = fields.Selection(
        selection=ACTIVITY_CODE_SELECTION,
        states=EDITABLE_ON_CALCULATED,
        string="Código 4ª actividad",
        readonly=True,
    )
    other_fourth_activity_iae = fields.Char(
        string="Epígrafe I.A.E. 4ª actividad",
        readonly=True,
        size=4,
        states=EDITABLE_ON_CALCULATED,
    )
    other_fifth_activity = fields.Char(
        string="5ª actividad", readonly=True, size=40, states=EDITABLE_ON_CALCULATED,
    )
    other_fifth_activity_code = fields.Selection(
        selection=ACTIVITY_CODE_SELECTION,
        states=EDITABLE_ON_CALCULATED,
        string="Código 5ª actividad",
        readonly=True,
    )
    other_fifth_activity_iae = fields.Char(
        string="Epígrafe I.A.E. 5ª actividad",
        readonly=True,
        size=4,
        states=EDITABLE_ON_CALCULATED,
    )
    # 4. Representantes
    first_representative_name = fields.Char(
        string="Nombre del primer representante",
        readonly=True,
        size=80,
        states=REQUIRED_ON_CALCULATED,
        help=REPRESENTATIVE_HELP,
    )
    first_representative_vat = fields.Char(
        string="NIF del primer representante",
        readonly=True,
        size=9,
        states=REQUIRED_ON_CALCULATED,
    )
    first_representative_date = fields.Date(
        string="Fecha poder del primer representante",
        readonly=True,
        states=EDITABLE_ON_CALCULATED,
    )
    first_representative_notary = fields.Char(
        string="Notaría del primer representante",
        readonly=True,
        size=12,
        help=NOTARY_CODE_HELP,
        states=EDITABLE_ON_CALCULATED,
    )
    second_representative_name = fields.Char(
        string="Nombre del segundo representante",
        readonly=True,
        size=80,
        states=EDITABLE_ON_CALCULATED,
        help=REPRESENTATIVE_HELP,
    )
    second_representative_vat = fields.Char(
        string="NIF del segundo representante",
        readonly=True,
        size=9,
        states=EDITABLE_ON_CALCULATED,
    )
    second_representative_date = fields.Date(
        string="Fecha poder del segundo representante",
        readonly=True,
        states=EDITABLE_ON_CALCULATED,
    )
    second_representative_notary = fields.Char(
        string="Notaría del segundo representante",
        readonly=True,
        size=12,
        states=EDITABLE_ON_CALCULATED,
        help=NOTARY_CODE_HELP,
    )
    third_representative_name = fields.Char(
        string="Nombre del tercer representante",
        readonly=True,
        size=80,
        states=EDITABLE_ON_CALCULATED,
        help=REPRESENTATIVE_HELP,
    )
    third_representative_vat = fields.Char(
        string="NIF del tercer representante",
        readonly=True,
        size=9,
        states=EDITABLE_ON_CALCULATED,
    )
    third_representative_date = fields.Date(
        string="Fecha poder del tercer representante",
        readonly=True,
        states=EDITABLE_ON_CALCULATED,
    )
    third_representative_notary = fields.Char(
        string="Notaría del tercer representante",
        readonly=True,
        size=12,
        states=EDITABLE_ON_CALCULATED,
        help=NOTARY_CODE_HELP,
    )
    # 5. Régimen general
    casilla_33 = fields.Float(
        compute="_compute_casilla_33", string="[33] Total bases IVA", store=True,
    )
    casilla_34 = fields.Float(
        compute="_compute_casilla_34", string="[34] Total cuotas IVA", store=True,
    )
    casilla_47 = fields.Float(
        compute="_compute_casilla_47",
        store=True,
        string="[47] Total cuotas IVA y recargo de equivalencia",
    )
    casilla_48 = fields.Float(
        compute="_compute_casilla_48",
        store=True,
        string="[48] Total base deducible operaciones corrientes",
    )
    casilla_49 = fields.Float(
        compute="_compute_casilla_49",
        store=True,
        string="[49] Total cuota deducible operaciones corrientes",
    )
    casilla_50 = fields.Float(
        compute="_compute_casilla_50",
        store=True,
        string="[50] Total bases imponibles deducibles en operaciones "
        "interiores de bienes de inversión",
    )
    casilla_51 = fields.Float(
        compute="_compute_casilla_51",
        store=True,
        string="[51] Total de cuotas deducibles en operaciones interiores de "
        "bienes de inversión",
    )
    casilla_52 = fields.Float(
        compute="_compute_casilla_52",
        store=True,
        string="[52] Total base deducible importaciones corrientes",
    )
    casilla_53 = fields.Float(
        compute="_compute_casilla_53",
        store=True,
        string="[53] Total cuota deducible importaciones corrientes",
    )
    casilla_54 = fields.Float(
        compute="_compute_casilla_54",
        store=True,
        string="[54] Total base deducible importaciones bienes de inversión",
    )
    casilla_55 = fields.Float(
        compute="_compute_casilla_55",
        store=True,
        string="[55] Total cuota deducible importaciones bienes de inversión",
    )
    casilla_56 = fields.Float(
        compute="_compute_casilla_56",
        store=True,
        string="[56] Total base deducible adq. intracomunitarias bienes",
    )
    casilla_57 = fields.Float(
        compute="_compute_casilla_57",
        store=True,
        string="[57] Total cuota deducible adq. intracomunitarias bienes",
    )
    casilla_58 = fields.Float(
        compute="_compute_casilla_58",
        store=True,
        string="[58] Total base deducible adq. intracomunitarias bienes de "
        "inversión",
    )
    casilla_59 = fields.Float(
        compute="_compute_casilla_59",
        store=True,
        string="[59] Total cuota deducible adq. intracomunitarias bienes de "
        "inversión",
    )
    casilla_597 = fields.Float(
        compute="_compute_casilla_597",
        store=True,
        string="[597] Total base deducible adq. intracomunitarias servicios",
    )
    casilla_598 = fields.Float(
        compute="_compute_casilla_598",
        store=True,
        string="[598] Total cuota deducible adq. intracomunitarias servicios",
    )
    casilla_64 = fields.Float(
        compute="_compute_casilla_64", store=True, string="[64] Suma de deducciones",
    )
    casilla_65 = fields.Float(
        compute="_compute_casilla_65", store=True, string="[65] Result. rég. gral.",
    )
    casilla_85 = fields.Float(
        string="[85] Compens. ejercicio anterior",
        readonly=True,
        states=EDITABLE_ON_CALCULATED,
        help="Si en la autoliquidación del último período del ejercicio "
        "anterior resultó un saldo a su favor y usted optó por la "
        "compensación, consigne en esta casilla la cantidad a "
        "compensar, salvo que la misma haya sido modificada por la "
        "Administración, en cuyo caso se consignará esta última.",
    )
    casilla_86 = fields.Float(
        compute="_compute_casilla_86", store=True, string="[86] Result. liquidación",
    )
    # 9. Resultado de las liquidaciones
    casilla_95 = fields.Float(
        string="[95] Total resultados a ingresar modelo 303",
        help="Se consignará la suma de las cantidades a ingresar por el "
        "Impuesto como resultado de las autoliquidaciones periódicas "
        "del ejercicio que no tributen en el régimen especial del grupo "
        "de entidades, incluyendo aquellas para las que se hubiese "
        "solicitado aplazamiento, fraccionamiento o no se hubiese "
        "efectuado el pago.",
        states=REQUIRED_ON_CALCULATED,
        readonly=True,
    )
    casilla_97 = fields.Float(
        string="[97] Result. 303 último periodo a compensar",
        help="Si el resultado de la última autoliquidación fue a compensar, "
        "consignará en esta casilla el importe de la misma.",
        states=REQUIRED_ON_CALCULATED,
        readonly=True,
    )
    casilla_98 = fields.Float(
        string="[98] Result. 303 último periodo a devolver",
        help="Si el resultado de la última autoliquidación fue a devolver, "
        "consignará en esta casilla el importe de la misma.",
        states=REQUIRED_ON_CALCULATED,
        readonly=True,
    )
    casilla_108 = fields.Float(
        string="[108] Total vol. oper.", compute="_compute_casilla_108", store=True,
    )

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_33(self):
        for report in self:
            report.casilla_33 = sum(
                report.tax_line_ids.filtered(
                    lambda x: x.field_number
                    in (
                        1,
                        3,
                        5,  # Régimen ordinario
                        500,
                        502,
                        504,  # Intragrupo - no incluido aún
                        643,
                        645,
                        647,  # Criterio de caja - no incluido aún
                        7,
                        9,
                        11,  # Bienes usados, etc - no incluido aún
                        13,  # Agencias de viajes - no incluido aún
                        21,
                        23,
                        25,  # Adquis. intracomunitaria bienes
                        545,
                        547,
                        551,  # Adquis. intracomunitaria servicios
                        27,  # IVA otras operaciones sujeto pasivo
                        29,  # Modificación bases y cuotas
                        649,  # Modif. bases y cuotas intragrupo - no incluido aún
                        31,  # Modif. bases y cuotas concurso ac. - no incluido aún
                    )
                ).mapped("amount")
            )

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_34(self):
        for report in self:
            report.casilla_34 = sum(
                report.tax_line_ids.filtered(
                    lambda x: x.field_number
                    in (
                        2,
                        4,
                        6,  # Régimen ordinario
                        501,
                        503,
                        505,  # Intragrupo - no incluido aún
                        644,
                        646,
                        648,  # Criterio de caja - no incluido aún
                        8,
                        10,
                        12,  # Bienes usados, etc - no incluido aún
                        14,  # Agencias de viajes - no incluido aún
                        22,
                        24,
                        26,  # Adquis. intracomunitaria bienes
                        546,
                        548,
                        552,  # Adquis. intracomunitaria servicios
                        28,  # IVA otras operaciones sujeto pasivo
                        30,  # Modificación bases y cuotas
                        650,  # Modif. bases y cuotas intragrupo - no incluido aún
                        32,  # Modif. bases y cuotas concurso ac. - no incluido aún
                    )
                ).mapped("amount")
            )

    @api.depends("casilla_34", "tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_47(self):
        for report in self:
            report.casilla_47 = report.casilla_34 + sum(
                report.tax_line_ids.filtered(
                    lambda x: x.field_number
                    in (
                        36,
                        600,
                        602,  # Recargo de equivalencia
                        44,  # Modificación recargo de equivalencia
                        46,  # Mod. recargo equiv. concurso - no incluido aún
                    )
                ).mapped("amount")
            )

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_38(self):
        for report in self:
            report.casilla_38 = sum(
                report.tax_line_ids.filtered(
                    lambda x: x.field_number in (190, 192, 555, 603, 194, 557, 605)
                ).mapped("amount")
            )

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_39(self):
        for report in self:
            report.casilla_39 = sum(
                report.tax_line_ids.filtered(
                    lambda x: x.field_number in (191, 193, 556, 604, 195, 558, 606)
                ).mapped("amount")
            )

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_48(self):
        for report in self:
            report.casilla_48 = sum(
                report.tax_line_ids.filtered(
                    lambda x: x.field_number in (190, 192, 555, 603, 194, 557, 605)
                ).mapped("amount")
            )

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_49(self):
        for report in self:
            report.casilla_49 = sum(
                report.tax_line_ids.filtered(
                    lambda x: x.field_number in (191, 193, 556, 604, 195, 558, 606)
                ).mapped("amount")
            )

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_50(self):
        for report in self:
            report.casilla_50 = sum(
                report.tax_line_ids.filtered(
                    lambda x: x.field_number in (196, 611, 613)
                ).mapped("amount")
            )

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_51(self):
        for report in self:
            report.casilla_51 = sum(
                report.tax_line_ids.filtered(
                    lambda x: x.field_number in (197, 612, 614)
                ).mapped("amount")
            )

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_52(self):
        for report in self:
            report.casilla_52 = sum(
                report.tax_line_ids.filtered(
                    lambda x: x.field_number in (202, 204, 571, 619, 206, 573, 621)
                ).mapped("amount")
            )

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_53(self):
        for report in self:
            report.casilla_53 = sum(
                report.tax_line_ids.filtered(
                    lambda x: x.field_number in (203, 205, 572, 620, 207, 574, 622)
                ).mapped("amount")
            )

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_54(self):
        for report in self:
            report.casilla_54 = sum(
                report.tax_line_ids.filtered(
                    lambda x: x.field_number in (208, 623, 625)
                ).mapped("amount")
            )

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_55(self):
        for report in self:
            report.casilla_55 = sum(
                report.tax_line_ids.filtered(
                    lambda x: x.field_number in (209, 624, 626)
                ).mapped("amount")
            )

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_56(self):
        for report in self:
            report.casilla_56 = sum(
                report.tax_line_ids.filtered(
                    lambda x: x.field_number in (214, 216, 579, 627, 218, 581, 629)
                ).mapped("amount")
            )

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_57(self):
        for report in self:
            report.casilla_57 = sum(
                report.tax_line_ids.filtered(
                    lambda x: x.field_number in (215, 217, 580, 628, 219, 582, 630)
                ).mapped("amount")
            )

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_58(self):
        for report in self:
            report.casilla_58 = sum(
                report.tax_line_ids.filtered(
                    lambda x: x.field_number in (220, 631, 633)
                ).mapped("amount")
            )

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_59(self):
        for report in self:
            report.casilla_59 = sum(
                report.tax_line_ids.filtered(
                    lambda x: x.field_number in (221, 632, 634)
                ).mapped("amount")
            )

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_597(self):
        for report in self:
            report.casilla_597 = sum(
                report.tax_line_ids.filtered(
                    lambda x: x.field_number in (587, 589, 591, 635, 593, 595, 637)
                ).mapped("amount")
            )

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_598(self):
        for report in self:
            report.casilla_598 = sum(
                report.tax_line_ids.filtered(
                    lambda x: x.field_number in (588, 590, 592, 636, 594, 596, 638)
                ).mapped("amount")
            )

    @api.depends(
        "casilla_49",
        "casilla_51",
        "casilla_53",
        "casilla_55",
        "casilla_57",
        "casilla_59",
        "casilla_598",
        "tax_line_ids",
        "tax_line_ids.amount",
    )
    def _compute_casilla_64(self):
        for report in self:
            report.casilla_64 = (
                report.casilla_49
                + report.casilla_51
                + report.casilla_53
                + report.casilla_55
                + report.casilla_57
                + report.casilla_59
                + report.casilla_598
                + sum(
                    report.tax_line_ids.filtered(lambda x: x.field_number == 62).mapped(
                        "amount"
                    )
                )
            )

    @api.depends("casilla_47", "casilla_64")
    def _compute_casilla_65(self):
        for report in self:
            report.casilla_65 = report.casilla_47 - report.casilla_64

    @api.depends("casilla_65", "casilla_85")
    def _compute_casilla_86(self):
        for report in self:
            # It takes 65 instead of 84 + 659 as the rest are 0
            report.casilla_86 = report.casilla_65 - report.casilla_85

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_108(self):
        for report in self:
            report.casilla_108 = sum(
                report.tax_line_ids.filtered(
                    lambda x: x.field_number
                    in (99, 653, 103, 104, 105, 110, 112, 100, 101, 102, 227, 228)
                ).mapped("amount")
            ) - sum(
                report.tax_line_ids.filtered(
                    lambda x: x.field_number in (106, 107)
                ).mapped("amount")
            )

    @api.constrains("statement_type")
    def _check_type(self):
        if "C" in self.mapped("statement_type"):
            raise exceptions.UserError(
                _("You cannot make complementary reports for this model.")
            )

    def button_confirm(self):
        """Check that the manual 303 results match the report."""
        self.ensure_one()
        summary = self.casilla_95 - self.casilla_97 - self.casilla_98
        if float_compare(summary, self.casilla_86, precision_digits=2) != 0:
            raise exceptions.UserError(
                _(
                    "The result of the manual 303 summary (fields [95], [97] and "
                    "[98] in the page '9. Resultado liquidaciones') doesn't match "
                    "the field [86]. Please check if you have filled such fields."
                )
            )
        return super().button_confirm()
