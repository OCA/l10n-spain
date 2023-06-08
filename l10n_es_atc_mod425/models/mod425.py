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
]
REPRESENTATIVE_HELP = _("Nombre y apellidos del representante")
NOTARY_CODE_HELP = _(
    "Código de la notaría en la que se concedió el poder de representación "
    "para esta persona."
)


class L10nEsAtcMod425Report(models.Model):
    _description = "ATC 425 report"
    _inherit = "l10n.es.aeat.report.tax.mapping"
    _name = "l10n.es.atc.mod425.report"
    _aeat_number = "425"
    _period_quarterly = False
    _period_monthly = False
    _period_yearly = True

    # 3. Datos estadísticos
    has_415 = fields.Boolean(
        string="¿Obligación del 415?",
        default=True,
        help="Marque la casilla si el sujeto pasivo ha efectuado con alguna "
        "persona o entidad operaciones por las que tenga obligación de "
        "presentar la declaración anual de operaciones con terceras "
        "personas (modelo 415).",
    )
    main_activity = fields.Char(
        string="Actividad principal",
        readonly=True,
        size=40,
        states=REQUIRED_ON_CALCULATED,
    )
    main_activity_code = fields.Selection(
        selection=ACTIVITY_CODE_SELECTION,
        string="Clave",
    )
    main_regime_code_id = fields.Many2one(
        comodel_name="l10n.es.atc.mod425.report.regime.code",
        string="Régimen aplicable/Código",
    )
    main_activity_iae = fields.Char(
        string="Epígrafe I.A.E. actividad principal",
        readonly=True,
        size=4,
        states=REQUIRED_ON_CALCULATED,
    )
    other_first_activity = fields.Char(
        string="1ª actividad",
        readonly=True,
        size=40,
        states=EDITABLE_ON_CALCULATED,
    )
    other_first_activity_code = fields.Selection(
        selection=ACTIVITY_CODE_SELECTION,
        string="Código 1ª actividad (antiguo)",
        readonly=True,
    )
    other_first_activity_code_id = fields.Many2one(
        comodel_name="l10n.es.atc.mod425.report.regime.code",
        string="Código 1ª régimen",
    )
    other_first_activity_iae = fields.Char(
        string="Epígrafe I.A.E. 1ª régimen",
        readonly=True,
        size=4,
        states=EDITABLE_ON_CALCULATED,
    )
    # Prorrata Especial
    other_first_activity_pro_prorrata = fields.Integer(
        "% Provisional de la prorrata genera"
    )
    other_first_activity_def_prorrata = fields.Integer(
        "% Definitivo de la prorrata genera"
    )
    other_first_activity_esp_prorrata = fields.Boolean(
        "% Especial de la prorrata genera"
    )

    other_second_activity = fields.Char(
        string="2ª actividad",
        readonly=True,
        size=40,
        states=EDITABLE_ON_CALCULATED,
    )
    other_second_activity_code = fields.Selection(
        selection=ACTIVITY_CODE_SELECTION,
        states=EDITABLE_ON_CALCULATED,
        string="Código 2ª régimen",
        readonly=True,
    )
    other_second_activity_code_id = fields.Many2one(
        comodel_name="l10n.es.atc.mod425.report.regime.code",
        string="Código 2ª régimen",
    )
    other_second_activity_iae = fields.Char(
        string="Epígrafe I.A.E. 2ª régimen",
        readonly=True,
        size=4,
        states=EDITABLE_ON_CALCULATED,
    )
    # Prorrata Especial
    other_second_activity_pro_prorrata = fields.Integer(
        "% Provisional de la prorrata genera"
    )
    other_second_activity_def_prorrata = fields.Integer(
        "% Definitivo de la prorrata genera"
    )
    other_second_activity_esp_prorrata = fields.Boolean(
        "% Especial de la prorrata genera"
    )
    other_third_activity = fields.Char(
        string="3ª actividad",
        readonly=True,
        size=40,
        states=EDITABLE_ON_CALCULATED,
    )
    other_third_activity_code = fields.Selection(
        selection=ACTIVITY_CODE_SELECTION,
        states=EDITABLE_ON_CALCULATED,
        string="Código 3ª actividad (antiguo)",
    )
    other_third_activity_code_id = fields.Many2one(
        comodel_name="l10n.es.atc.mod425.report.regime.code",
        string="Código 3ª régimen",
    )
    other_third_activity_iae = fields.Char(
        string="Epígrafe I.A.E. 3ª régimen",
        readonly=True,
        size=4,
        states=EDITABLE_ON_CALCULATED,
    )
    # Prorrata Especial
    other_third_activity_pro_prorrata = fields.Integer(
        "% Provisional de la prorrata genera"
    )
    other_third_activity_def_prorrata = fields.Integer(
        "% Definitivo de la prorrata genera"
    )
    other_third_activity_esp_prorrata = fields.Boolean(
        "% Especial de la prorrata genera"
    )
    other_fourth_activity = fields.Char(
        string="4ª actividad",
        readonly=True,
        size=40,
        states=EDITABLE_ON_CALCULATED,
    )
    other_fourth_activity_code = fields.Selection(
        selection=ACTIVITY_CODE_SELECTION,
        states=EDITABLE_ON_CALCULATED,
        string="Código 4ª actividad (antiguo)",
    )
    other_fourth_activity_code_id = fields.Many2one(
        comodel_name="l10n.es.atc.mod425.report.regime.code",
        string="Código 4ª régimen",
    )
    other_fourth_activity_iae = fields.Char(
        string="Epígrafe I.A.E. 4ª régimen",
        readonly=True,
        size=4,
        states=EDITABLE_ON_CALCULATED,
    )
    # Prorrata Especial
    other_fourth_activity_pro_prorrata = fields.Integer(
        "% Provisional de la prorrata genera"
    )
    other_fourth_activity_def_prorrata = fields.Integer(
        "% Definitivo de la prorrata genera"
    )
    other_fourth_activity_esp_prorrata = fields.Boolean(
        "% Especial de la prorrata genera"
    )
    other_fifth_activity = fields.Char(
        string="5ª actividad",
        readonly=True,
        size=40,
        states=EDITABLE_ON_CALCULATED,
    )
    other_fifth_activity_code = fields.Selection(
        selection=ACTIVITY_CODE_SELECTION,
        states=EDITABLE_ON_CALCULATED,
        string="Código 5ª actividad (antiguo)",
        readonly=True,
    )
    other_fifth_activity_code_id = fields.Many2one(
        comodel_name="l10n.es.atc.mod425.report.regime.code",
        string="Código 5ª régimen",
    )
    other_fifth_activity_iae = fields.Char(
        string="Epígrafe I.A.E. 5ª régimen",
        readonly=True,
        size=4,
        states=EDITABLE_ON_CALCULATED,
    )
    # Prorrata Especial
    other_fifth_activity_pro_prorrata = fields.Integer(
        "% Provisional de la prorrata genera"
    )
    other_fifth_activity_def_prorrata = fields.Integer(
        "% Definitivo de la prorrata genera"
    )
    other_fifth_activity_esp_prorrata = fields.Boolean(
        "% Especial de la prorrata genera"
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
    
    casilla_72 = fields.Float(
        string="[72] Modificación de Bases por procedimientos de concurso "
        "de acreedores o créditos incobrables",
        readonly=True,
        states=EDITABLE_ON_CALCULATED,
    )
    casilla_73 = fields.Float(
        string="[73] Modificación de Cuotas por procedimientos de concurso "
        "de acreedores o créditos incobrables",
        readonly=True,
        states=EDITABLE_ON_CALCULATED,
    )
    # 5. Régimen general
    casilla_74 = fields.Float(
        compute="_compute_casilla_74",
        string="[74] Total bases IGIC",
        store=True,
    )
    casilla_75 = fields.Float(
        string="[75] Operaciones con inversión del sujeto pasivo Cuotas",
        readonly=True,
        states=EDITABLE_ON_CALCULATED,
    )
    casilla_76 = fields.Float(
        string="[76] Operaciones con inversión del sujeto pasivo Bases",
        readonly=True,
        states=EDITABLE_ON_CALCULATED,
    )
    casilla_77 = fields.Float(
        string="[77] Régimen de viajeros Bases",
        readonly=True,
        states=EDITABLE_ON_CALCULATED,
    )
    casilla_78 = fields.Float(
        string="[78] Régimen de viajeros Cuotas",
        readonly=True,
        states=EDITABLE_ON_CALCULATED,
    )
    casilla_79 = fields.Float(
        compute="_compute_casilla_79",
        string="[79] Total cuotas IGIC",
        store=True,
    )
    casilla_90 = fields.Float(
        string="[90] Compensación régimen especial de agricultura, "
        "ganadería y pesca",
        readonly=True,
        states=EDITABLE_ON_CALCULATED,
    )
    casilla_91 = fields.Float(
        string="[91] Regularización de cuotas soportadas por bienes " "de inversión",
        readonly=True,
        states=EDITABLE_ON_CALCULATED,
    )
    casilla_92 = fields.Float(
        string="[92] Regularización de cuotas soportadas antes del "
        "inicio de la actividad",
        readonly=True,
        states=EDITABLE_ON_CALCULATED,
    )
    casilla_93 = fields.Float(
        string="[93] Regularización por aplicación del porcentaje "
        "definitivo de prorrata",
        readonly=True,
        states=EDITABLE_ON_CALCULATED,
    )
    casilla_94 = fields.Float(
        compute="_compute_casilla_94",
        string="[94] Total cuotas IGIC",
        store=True,
    )
    casilla_95 = fields.Float(
        compute="_compute_casilla_95",
        string="[95] Resultado régimen general",
        store=True,
    )

    # RESULTADO DE LA LIQUIDACIÓN ANUAL
    casilla_112 = fields.Float(
        string="[112] Regularización cuotas artículo 22.8.5ª Ley 20/1991",
        readonly=True,
        states=EDITABLE_ON_CALCULATED,
    )
    casilla_113 = fields.Float(
        compute="_compute_casilla_113",
        string="[113] Suma de resultados",
        store=True,
    )
    casilla_114 = fields.Float(
        string="[114] Cuota de IGIC a compensar del ejercicio anterior",
        readonly=True,
        states=EDITABLE_ON_CALCULATED,
    )
    casilla_115 = fields.Float(
        compute="_compute_casilla_115",
        string="[115] Resultado de la liquidación anual",
        store=True,
    )

    # RESULTADO DE LAS AUTOLIQUIDACIONES
    casilla_116 = fields.Float(
        string="[116] Total de ingresos realizados en las autoliquidaciones "
        "por IGIC del ejercicio",
        readonly=True,
        states=EDITABLE_ON_CALCULATED,
    )
    casilla_117 = fields.Float(
        string="[117] Total devoluciones mensuales por IGIC a sujetos pasivos "
        "inscritos en el Registro de Devolución Mensual",
        readonly=True,
        states=EDITABLE_ON_CALCULATED,
    )
    casilla_118 = fields.Float(
        string="[118] A compensar",
        readonly=True,
        states=EDITABLE_ON_CALCULATED,
        help="si el resultado de la última autoliquidación del año fue a "
        "compensar, consigne en esta casilla el importe de la misma",
    )
    casilla_119 = fields.Float(
        string="[119] A devolver",
        readonly=True,
        states=EDITABLE_ON_CALCULATED,
        help="si el resultado de la última autoliquidación del año fue a "
        "compensar, consigne en esta casilla el importe de la misma.",
    )

    casilla_120 = fields.Float(
        string="[120] Total vol. oper.",
        compute="_compute_casilla_120",
        store=True,
    )

    ###############################################

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_74(self):
        for report in self:
            report.casilla_74 = (
                sum(
                    report.tax_line_ids.filtered(
                        lambda x: x.field_number
                        in (
                            1,
                            4,
                            7,
                            10,
                            13,
                            16,  # Régimen ordinario
                            19,
                            22,
                            25,
                            28,
                            31,  # Bienes usados, etc - no incluido aún
                            34,
                            37,
                            40,
                            43,
                            46,  # Régimen especial de objetos - no incluido año
                            49,
                            52,
                            55,
                            58,
                            61,
                            64,  # Criterio de caja - no incluido aún
                            67,  # Agencias de viajes - no incluido aún
                            70,  # Modificación bases y cuotas
                        )
                    ).mapped("amount")
                )
                - report.casilla_72
            )

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_79(self):
        for report in self:
            report.casilla_79 = (
                sum(
                    report.tax_line_ids.filtered(
                        lambda x: x.field_number
                        in (
                            3,
                            6,
                            9,
                            12,
                            15,
                            18,  # Régimen ordinario
                            21,
                            24,
                            27,
                            30,
                            33,  # Bienes usados, etc - no incluido aún
                            36,
                            39,
                            42,
                            45,
                            48,  # Régimen especial de objetos -  no incluido año
                            51,
                            54,
                            57,
                            60,
                            63,
                            66,  # Criterio de caja - no incluido aún
                            69,  # Agencias de viajes - no incluido aún
                            71,  # Modificación bases y cuotas
                            76,
                        )
                    ).mapped("amount")
                )
                - report.casilla_73
                - report.casilla_78
            )

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_94(self):
        for report in self:
            report.casilla_94 = sum(
                report.tax_line_ids.filtered(
                    lambda x: x.field_number in (81, 83, 85, 87, 89, 90, 91, 92, 93)
                ).mapped("amount")
            )

    @api.depends("casilla_79", "casilla_94", "tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_95(self):
        for report in self:
            report.casilla_95 = report.casilla_79 - report.casilla_94

    @api.depends("casilla_95", "tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_113(self):
        for report in self:
            report.casilla_113 = report.casilla_95

    @api.depends(
        "casilla_74",
        "casilla_112",
        "casilla_114",
        "tax_line_ids",
        "tax_line_ids.amount",
    )
    def _compute_casilla_115(self):
        for report in self:
            report.casilla_115 = (
                report.casilla_112 + report.casilla_113 - report.casilla_114
            )

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_120(self):
        for report in self:
            report.casilla_120 = sum(
                report.tax_line_ids.filtered(lambda x: x.field_number == 120).mapped(
                    "amount"
                )
            )

    @api.constrains("statement_type")
    def _check_type(self):
        if "C" in self.mapped("statement_type"):
            raise exceptions.UserError(
                _("You cannot make complementary reports for this model.")
            )

    def button_confirm(self):
        """Check that the manual 420 results match the report."""
        self.ensure_one()
        summary = self.casilla_116 - self.casilla_118 - self.casilla_119
        if float_compare(summary, self.casilla_115, precision_digits=2) != 0:
            raise exceptions.UserError(
                _(
                    "The result of the manual 420 summary (fields [116], [118] and "
                    "[119] in the page '9. Resultado liquidaciones') doesn't match "
                    "the field [115]. Please check if you have filled such fields."
                )
            )
        return super().button_confirm()

    def button_modelo_sobre(self):
        self.ensure_one()
        url = str("/l10n_es_atc_mod425/static/src/pdf/caratula_sobre_425.pdf")
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "self",
            "tag": "reload",
        }


class L10nEsAtcMod425RegimeCode(models.Model):
    _name = "l10n.es.atc.mod425.report.regime.code"
    _order = "code,id"
    _description = "ATC Mod425 Regime Codes"

    code = fields.Char(string="Regime code", required=True)
    name = fields.Char(
        string="Regime name",
        translate=True,
        required=True,
    )


class L10nEsAtcMod425RegimeCode(models.Model):
    _name = "l10n.es.atc.mod425.report.key"
    _order = "code,id"
    _description = "ATC Mod425 Key"

    code = fields.Char(string="Key", required=True)
    name = fields.Char(
        string="Key name",
        translate=True,
        required=True,
    )
