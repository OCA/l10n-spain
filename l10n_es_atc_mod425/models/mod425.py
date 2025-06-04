# Copyright 2025 Tecnativa - Carlos Lopez
from odoo import _, api, exceptions, fields, models

from odoo.addons.l10n_es_atc.models.l10n_es_atc_report import ATC_JAR_URL

ATC_JAR_URL[
    "425"
] = "https://www3.gobiernodecanarias.org/tributos/atc/documents/d/agencia-tributaria-canaria/m425v620e24-zip"

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
REGIMEN_CODE_SELECTION = [
    ("1", "1: Régimen ordinario"),
    ("2", "2: Régimen especial de bienes usados"),
    (
        "3",
        "3: Régimen especial de objetos de arte, antigüedades y objetos de colección",
    ),
    ("4", "4: Régimen especial de comerciantes minoristas"),
    ("5", "5: Régimen especial simplificado"),
    ("6", "6: Régimen especial de la agricultura, ganadería y pesca"),
    ("7", "7: Régimen especial de agencias de viajes"),
    ("8", "8: Régimen especial aplicable a las operaciones con oro de inversión"),
    (
        "9",
        "9: Régimen especial del grupo de entidades",
    ),
    ("10", "10: Régimen especial del pequeño empresario o profesional"),
    ("11", "11: Régimen especial del criterio de caja"),
]
REPRESENTATIVE_HELP = _("Nombre y apellidos del representante")
NOTARY_CODE_HELP = _(
    "Código de la notaría en la que se concedió el poder de representación "
    "para esta persona."
)


class L10nEsAtcMod425Report(models.Model):
    _description = "ATC 425 report"
    _inherit = "l10n.es.atc.report"
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
    is_cash_basis = fields.Boolean(string="¿Criterio de caja?")
    main_activity_code = fields.Selection(
        selection=ACTIVITY_CODE_SELECTION,
        string="Clave",
    )
    main_regime_code = fields.Selection(
        selection=REGIMEN_CODE_SELECTION,
        string="Régimen aplicable/Código",
    )
    main_activity_iae = fields.Char(
        string="Epígrafe I.A.E. actividad principal",
        readonly=True,
        size=4,
    )
    main_activity_pro_prorrata = fields.Integer("% Provisional de la prorrata genera")
    main_activity_def_prorrata = fields.Integer("% Definitivo de la prorrata genera")
    main_activity_esp_prorrata = fields.Boolean("% Especial de la prorrata genera")
    other_first_activity_code = fields.Selection(
        selection=ACTIVITY_CODE_SELECTION,
        string="Clave 1ª actividad",
    )
    other_first_regime_code = fields.Selection(
        selection=REGIMEN_CODE_SELECTION,
        string="Código 1ª régimen",
    )
    other_first_activity_iae = fields.Char(
        string="Epígrafe I.A.E. 1ª régimen",
        size=4,
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
    other_second_activity_code = fields.Selection(
        selection=ACTIVITY_CODE_SELECTION,
        string="Clave 2ª actividad",
    )
    other_second_regime_code = fields.Selection(
        selection=REGIMEN_CODE_SELECTION,
        string="Código 2ª régimen",
    )
    other_second_activity_iae = fields.Char(
        string="Epígrafe I.A.E. 2ª régimen",
        size=4,
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
    other_third_activity_code = fields.Selection(
        selection=ACTIVITY_CODE_SELECTION,
        string="Clave 3ª actividad",
    )
    other_third_regime_code = fields.Selection(
        selection=REGIMEN_CODE_SELECTION,
        string="Código 3ª régimen",
    )
    other_third_activity_iae = fields.Char(string="Epígrafe I.A.E. 3ª régimen", size=4)
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
    other_fourth_activity_code = fields.Selection(
        selection=ACTIVITY_CODE_SELECTION,
        string="Clave 4ª actividad",
    )
    other_fourth_regime_code = fields.Selection(
        selection=REGIMEN_CODE_SELECTION,
        string="Código 4ª régimen",
    )
    other_fourth_activity_iae = fields.Char(string="Epígrafe I.A.E. 4ª régimen", size=4)
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
        size=40,
    )
    other_fifth_activity_code = fields.Selection(
        selection=ACTIVITY_CODE_SELECTION,
        string="Clave 5ª actividad",
    )
    other_fifth_regime_code = fields.Selection(
        selection=REGIMEN_CODE_SELECTION,
        string="Código 5ª régimen",
    )
    other_fifth_activity_iae = fields.Char(
        string="Epígrafe I.A.E. 5ª régimen",
        size=4,
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
        help=REPRESENTATIVE_HELP,
    )
    first_representative_vat = fields.Char(
        string="NIF del primer representante",
        readonly=True,
        size=9,
    )
    first_representative_date = fields.Date(
        string="Fecha poder del primer representante"
    )
    first_representative_notary = fields.Char(
        string="Notaría del primer representante", size=12, help=NOTARY_CODE_HELP
    )
    second_representative_name = fields.Char(
        string="Nombre del segundo representante",
        size=80,
        help=REPRESENTATIVE_HELP,
    )
    second_representative_vat = fields.Char(
        string="NIF del segundo representante",
        size=9,
    )
    second_representative_date = fields.Date(
        string="Fecha poder del segundo representante"
    )
    second_representative_notary = fields.Char(
        string="Notaría del segundo representante",
        size=12,
        help=NOTARY_CODE_HELP,
    )
    third_representative_name = fields.Char(
        string="Nombre del tercer representante",
        size=80,
        help=REPRESENTATIVE_HELP,
    )
    third_representative_vat = fields.Char(
        string="NIF del tercer representante", size=9
    )
    third_representative_date = fields.Date(
        string="Fecha poder del tercer representante"
    )
    third_representative_notary = fields.Char(
        string="Notaría del tercer representante",
        size=12,
        help=NOTARY_CODE_HELP,
    )

    casilla_72 = fields.Monetary(
        string="[72] Modificación de Bases por procedimientos de concurso "
        "de acreedores o créditos incobrables",
    )
    casilla_73 = fields.Monetary(
        string="[73] Modificación de Cuotas por procedimientos de concurso "
        "de acreedores o créditos incobrables",
    )
    # 5. Régimen general
    casilla_74 = fields.Monetary(
        compute="_compute_casilla_74",
        string="[74] Total bases IGIC",
        store=True,
    )
    casilla_75 = fields.Monetary(
        string="[75] Operaciones con inversión del sujeto pasivo Bases"
    )
    casilla_76 = fields.Monetary(
        string="[76] Operaciones con inversión del sujeto pasivo Cuotas"
    )
    casilla_77 = fields.Monetary(string="[77] Régimen de viajeros Bases")
    casilla_78 = fields.Monetary(string="[78] Régimen de viajeros Cuotas")
    casilla_79 = fields.Monetary(
        compute="_compute_casilla_79",
        string="[79] Total cuotas IGIC",
        store=True,
    )
    casilla_90 = fields.Monetary(
        string="[90] Compensación régimen especial de agricultura, " "ganadería y pesca"
    )
    casilla_91 = fields.Monetary(
        string="[91] Regularización de cuotas soportadas por bienes " "de inversión"
    )
    casilla_92 = fields.Monetary(
        string="[92] Regularización de cuotas soportadas antes del "
        "inicio de la actividad",
    )
    casilla_93 = fields.Monetary(
        string="[93] Regularización por aplicación del porcentaje "
        "definitivo de prorrata"
    )
    casilla_94 = fields.Monetary(
        compute="_compute_casilla_94",
        string="[94] Total cuotas IGIC",
        store=True,
    )
    casilla_95 = fields.Monetary(
        compute="_compute_casilla_95",
        string="[95] Resultado régimen general",
        store=True,
    )

    # RESULTADO DE LA LIQUIDACIÓN ANUAL
    casilla_112 = fields.Monetary(
        string="[112] Regularización cuotas artículo 22.8.5ª Ley 20/1991"
    )
    casilla_113 = fields.Monetary(
        compute="_compute_casilla_113",
        string="[113] Suma de resultados",
        store=True,
    )
    casilla_114 = fields.Monetary(
        string="[114] Cuota de IGIC a compensar del ejercicio anterior"
    )
    casilla_115 = fields.Monetary(
        compute="_compute_casilla_115",
        string="[115] Resultado de la liquidación anual",
        store=True,
    )

    # RESULTADO DE LAS AUTOLIQUIDACIONES
    casilla_116 = fields.Monetary(
        string="[116] Total de ingresos realizados en las autoliquidaciones "
        "por IGIC del ejercicio",
    )
    casilla_117 = fields.Monetary(
        string="[117] Total devoluciones mensuales por IGIC a sujetos pasivos "
        "inscritos en el Registro de Devolución Mensual"
    )
    casilla_118 = fields.Monetary(
        string="[118] A compensar",
        help="si el resultado de la última autoliquidación del año fue a "
        "compensar, consigne en esta casilla el importe de la misma",
    )
    casilla_119 = fields.Monetary(
        string="[119] A devolver",
        help="si el resultado de la última autoliquidación del año fue a "
        "compensar, consigne en esta casilla el importe de la misma.",
    )

    casilla_120 = fields.Monetary(
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
                            46,  # Régimen especial de objetos - no incluido aún
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

    @api.depends(
        "tax_line_ids", "tax_line_ids.amount", "casilla_73", "casilla_76", "casilla_78"
    )
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
                            48,  # Régimen especial de objetos -  no incluido aún
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
                + report.casilla_76
                - report.casilla_78
            )

    @api.depends(
        "tax_line_ids",
        "tax_line_ids.amount",
        "casilla_90",
        "casilla_91",
        "casilla_92",
        "casilla_93",
    )
    def _compute_casilla_94(self):
        for report in self:
            report.casilla_94 = sum(
                report.tax_line_ids.filtered(
                    lambda x: x.field_number in (81, 83, 85, 87, 89)
                ).mapped("amount")
            )
            report.casilla_94 += (
                report.casilla_90
                + report.casilla_91
                + report.casilla_92
                + report.casilla_93
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

    @api.depends("casilla_74")
    def _compute_casilla_120(self):
        for report in self:
            report.casilla_120 = report.casilla_74

    @api.constrains("statement_type")
    def _check_type(self):
        if "C" in self.mapped("statement_type"):
            raise exceptions.UserError(
                _("You cannot make complementary reports for this model.")
            )

    def button_modelo_sobre(self):
        self.ensure_one()
        url = "/l10n_es_atc_mod425/static/src/pdf/caratula_sobre_425.pdf"
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "self",
            "tag": "reload",
        }

    def action_generar_mod425(self):
        self.ensure_one()
        self._atc_validate_fields()
        report_name = "l10n_es_atc_mod425.mod425_report_xml"
        # the jar filename to be used from .zip
        # downloaded from the url in ATC_JAR_URL
        jar_filename = "pa-mod425.jar"
        # the main class to be used from the jar file
        main_class = "org.grecasa.ext.pa.mod425.MIModelo425"
        # The filename of the report that the user will download
        filename = f"modelo{self._aeat_number}"
        # run the command and get the attachment
        attachment = self._atc_run_cmd(report_name, filename, jar_filename, main_class)
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{attachment.id}?download=true",
        }

    def _atc_get_messages(self):
        messages = super()._atc_get_messages()
        if not self.company_id.city_id.code:
            messages.append(
                _(
                    "- Please set the code in the city: %s",
                    self.company_id.city_id.display_name,
                )
            )
        if not self.company_id.atc_public_way:
            messages.append(
                _(
                    "- Please set the Public Way in the company",
                )
            )
        return messages
