# Copyright 2019 Creu Blanca
# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, exceptions, fields, models

from odoo.addons.l10n_es_aeat.models.spanish_states_mapping import SPANISH_STATES


class L10nEsAeatMod190Report(models.Model):
    _description = "AEAT 190 report"
    _inherit = "l10n.es.aeat.report.tax.mapping"
    _name = "l10n.es.aeat.mod190.report"
    _aeat_number = "190"
    _period_quarterly = False
    _period_monthly = False
    _period_yearly = True

    casilla_01 = fields.Integer(
        string="[01] Recipients",
        compute="_compute_casilla_01",
        readonly=False,
        store=True,
    )
    casilla_02 = fields.Float(
        string="[02] Amount of perceptions",
        compute="_compute_casilla_02",
        readonly=False,
        store=True,
    )
    casilla_03 = fields.Float(
        string="[03] Amount of retentions",
        compute="_compute_casilla_03",
        readonly=False,
        store=True,
    )
    partner_record_ids = fields.One2many(
        comodel_name="l10n.es.aeat.mod190.report.line",
        inverse_name="report_id",
        string="Partner records",
    )
    registro_manual = fields.Boolean(
        string="Manual records",
        default=False,
    )

    @api.depends("partner_record_ids")
    def _compute_casilla_01(self):
        for item in self:
            item.casilla_01 = len(item.partner_record_ids)

    @api.depends(
        "registro_manual",
        "partner_record_ids",
        "partner_record_ids.percepciones_dinerarias",
        "partner_record_ids.percepciones_en_especie",
        "partner_record_ids.percepciones_dinerarias_incap",
        "partner_record_ids.percepciones_en_especie_incap",
        "tax_line_ids",
    )
    def _compute_casilla_02(self):
        for item in self:
            value = 0
            if item.registro_manual:
                value += sum(item.mapped("partner_record_ids.percepciones_dinerarias"))
                value += sum(item.mapped("partner_record_ids.percepciones_en_especie"))
                value += sum(
                    item.mapped("partner_record_ids.percepciones_dinerarias_incap")
                )
                value += sum(
                    item.mapped("partner_record_ids.percepciones_en_especie_incap")
                )
            else:
                tax_lines = item.tax_line_ids.search(
                    [
                        ("field_number", "in", (11, 13, 15)),
                        ("model", "=", item._name),
                        ("res_id", "=", item.id),
                    ]
                )
                for move_line in tax_lines.move_line_ids:
                    value += move_line.debit - move_line.credit
            item.casilla_02 = value

    @api.depends(
        "registro_manual",
        "partner_record_ids",
        "partner_record_ids.retenciones_dinerarias",
        "partner_record_ids.retenciones_dinerarias_incap",
        "tax_line_ids",
    )
    def _compute_casilla_03(self):
        for item in self:
            value = 0
            if item.registro_manual:
                value += sum(item.mapped("partner_record_ids.retenciones_dinerarias"))
                value += sum(
                    item.mapped("partner_record_ids.retenciones_dinerarias_incap")
                )
            else:
                tax_lines = self.tax_line_ids.search(
                    [
                        ("field_number", "in", (12, 14, 16)),
                        ("model", "=", item._name),
                        ("res_id", "=", item.id),
                    ]
                )
                for move_line in tax_lines.move_line_ids:
                    value += move_line.credit - move_line.debit
            item.casilla_03 = value

    def _check_report_lines(self):
        """Checks if all the fields of all the report lines
        (partner records) are filled"""
        if any(not item.partner_record_ok for item in self.partner_record_ids):
            raise exceptions.UserError(
                _("All partner records fields (country, VAT number) " "must be filled.")
            )

    def button_confirm(self):
        self._check_report_lines()
        return super().button_confirm()

    def calculate(self):
        res = super().calculate()
        manual_records = self.filtered(lambda x: x.registro_manual)
        manual_records.partner_record_ids.unlink()
        for report in self - manual_records:
            tax_lines = report.tax_line_ids.filtered(
                lambda x: x.field_number in (11, 12, 13, 14, 15, 16)
                and x.res_id == report.id
            )
            tax_line_vals = {}
            partner_vals = []
            for line in tax_lines.move_line_ids:
                rp = line.partner_id
                key_id = line.aeat_perception_key_id or rp.aeat_perception_key_id
                subkey_id = (
                    line.aeat_perception_subkey_id or rp.aeat_perception_subkey_id
                )
                if rp.id not in tax_line_vals:
                    tax_line_vals[rp.id] = {}
                if key_id.id not in tax_line_vals[rp.id]:
                    tax_line_vals[rp.id][key_id.id] = {}
                if subkey_id.id not in tax_line_vals[rp.id][key_id.id]:
                    tax_line_vals[rp.id][key_id.id][subkey_id.id] = {}
                    if not rp.aeat_perception_key_id:
                        raise exceptions.UserError(
                            _(
                                "The perception key of the partner, %(partner)s. "
                                "Must be filled."
                            )
                            % ({"partner": rp.name})
                        )
                    values = report._get_line_mod190_vals(rp, key_id, subkey_id)
                    partner_vals.append(values)
                    tax_line_vals[rp.id][key_id.id][subkey_id.id] = values
            # Set partner_record_ids
            report.partner_record_ids = [(5, 0)] + [(0, 0, x) for x in partner_vals]
        return res

    def _get_line_mod190_vals(self, rp, key_id, subkey_id):
        codigo_provincia = SPANISH_STATES.get(rp.state_id.code)
        if not codigo_provincia:
            raise exceptions.UserError(
                _("The state is not defined in the partner, %s") % rp.name
            )
        return {
            "partner_id": rp.id,
            "aeat_perception_key_id": key_id.id,
            "aeat_perception_subkey_id": subkey_id.id,
        }


class L10nEsAeatMod190ReportLine(models.Model):
    _name = "l10n.es.aeat.mod190.report.line"
    _description = "Line for AEAT report Mod 190"

    report_id = fields.Many2one(
        comodel_name="l10n.es.aeat.mod190.report",
        string="AEAT 190 Report ID",
        ondelete="cascade",
    )
    partner_record_ok = fields.Boolean(
        compute="_compute_partner_record_ok",
        store=True,
        string="Partner Record OK",
        help="Checked if partner record is OK",
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner", string="Partner", required=True
    )
    partner_vat = fields.Char(string="NIF", compute="_compute_partner_vat", store=True)
    representante_legal_vat = fields.Char(
        string="L. R. VAT", compute="_compute_representante_legal_vat", store=True
    )
    aeat_perception_key_id = fields.Many2one(
        comodel_name="l10n.es.aeat.report.perception.key",
        string="Perception key",
        required=True,
    )
    aeat_perception_subkey_id = fields.Many2one(
        comodel_name="l10n.es.aeat.report.perception.subkey",
        string="Perception subkey",
    )
    ejercicio_devengo = fields.Char(string="year")
    ceuta_melilla = fields.Char(
        string="Ceuta or Melilla", related="partner_id.ceuta_melilla"
    )
    # Percepciones y Retenciones
    percepciones_dinerarias = fields.Float(
        string="Monetary perceptions",
        compute="_compute_percepciones_dinerarias",
        store=True,
    )
    retenciones_dinerarias = fields.Float(
        string="Money withholdings",
        compute="_compute_retenciones_dinerarias",
        store=True,
    )
    percepciones_en_especie = fields.Float(
        string="Valuation", compute="_compute_percepciones_en_especie", store=True
    )
    ingresos_a_cuenta_efectuados = fields.Float(
        string="Income paid on account",
        compute="_compute_ingresos_a_cuenta_efectuados",
        store=True,
    )
    ingresos_a_cuenta_repercutidos = fields.Float(
        string="Income paid into account",
        compute="_compute_ingresos_a_cuenta_repercutidos",
        store=True,
    )
    percepciones_dinerarias_incap = fields.Float(
        string="Monetary perceptions derived from incapacity for work",
        compute="_compute_percepciones_dinerarias_incap",
        store=True,
    )
    retenciones_dinerarias_incap = fields.Float(
        string="Monetary withholdings derived from incapacity for work",
        compute="_compute_retenciones_dinerarias_incap",
        store=True,
    )
    percepciones_en_especie_incap = fields.Float(
        string="Perceptions in kind arising from incapacity for work",
        compute="_compute_percepciones_en_especie_incap",
        store=True,
    )
    ingresos_a_cuenta_efectuados_incap = fields.Float(
        string="Income on account in kind made as a result of incapacity " "for work",
        compute="_compute_ingresos_a_cuenta_efectuados_incap",
        store=True,
    )
    ingresos_a_cuenta_repercutidos_incap = fields.Float(
        string="Income to account in kind, repercussions derived from "
        "incapacity for work",
        compute="_compute_ingresos_a_cuenta_repercutidos_incap",
        store=True,
    )
    codigo_provincia = fields.Char(
        string="State ISO code",
        compute="_compute_codigo_provincia",
        store=True,
    )
    # DATOS ADICIONALES (solo en las claves A, B.01, B.03, C, E.01 y E.02).
    a_nacimiento = fields.Char(
        string="Year of birth", compute="_compute_partner_id_ad_required", store=True
    )
    situacion_familiar = fields.Selection(
        selection=[
            (
                "1",
                "1 - Single, widowed, divorced or separated with children "
                "under 18 or incapacitated",
            ),
            (
                "2",
                "2 - Married and not legally separated and your spouse has "
                "no annual income above the amount referred to",
            ),
            ("3", "3 - Other."),
        ],
        string="Family situation",
        compute="_compute_partner_id_ad_required",
        store=True,
    )
    nif_conyuge = fields.Char(
        string="VAT of the spouse",
        compute="_compute_partner_id_ad_required",
        store=True,
    )
    discapacidad = fields.Selection(
        [
            ("0", "0 - No disability or degree of disability less than 33 percent."),
            (
                "1",
                "1 - Degree of disability greater than 33 percent and less than "
                "66 percent.",
            ),
            (
                "2",
                "2 - Degree of disability greater than 33 percent and less than "
                "66 percent, and reduced mobility.",
            ),
            ("3", "3 - Degree of disability equal to or greater than 65%."),
        ],
        string="Disability",
        compute="_compute_partner_id_ad_required",
        store=True,
    )
    contrato_o_relacion = fields.Selection(
        selection=[
            ("1", "1 - Contract or relationship of a general nature"),
            ("2", "2 - Contract or ratio less than a year"),
            (
                "3",
                "3 - Contract or special employment relationship of a dependent "
                "nature",
            ),
            ("4", "4 - Sporadic relationship of manual workers"),
        ],
        string="Contract or relationship",
        compute="_compute_partner_id_ad_required",
        store=True,
    )
    movilidad_geografica = fields.Selection(
        selection=[("0", "NO"), ("1", "SI")],
        string="Geographical mobility",
        compute="_compute_partner_id_ad_required",
        store=True,
    )
    reduccion_aplicable = fields.Float(string="Applicable reduction")
    gastos_deducibles = fields.Float(string="Deductible expenses")
    pensiones_compensatorias = fields.Float(string="Compensatory pensions")
    anualidades_por_alimentos = fields.Float(string="Annuities for food")
    prestamos_vh = fields.Selection(
        selection=[
            (
                "0",
                "0 - Si en ningún momento del ejercicio ha resultado de "
                "aplicación la reducción del tipo de retención.",
            ),
            (
                "1",
                "1 - Si en algún momento del ejercicio ha resultado de "
                "aplicación la reducción del tipo de retención.",
            ),
        ],
        string="Comunicación préstamos vivienda habitual",
    )
    hijos_y_descendientes_m = fields.Integer(
        string="Under 3 years", compute="_compute_partner_id_ad_required", store=True
    )
    hijos_y_descendientes_m_entero = fields.Integer(
        string="Under 3 years, computed entirely",
        compute="_compute_partner_id_ad_required",
        store=True,
    )
    hijos_y_descendientes = fields.Integer(
        string="Rest", compute="_compute_partner_id_ad_required", store=True
    )
    hijos_y_descendientes_entero = fields.Integer(
        string="Rest, computed entirely",
        compute="_compute_partner_id_ad_required",
        store=True,
    )
    hijos_y_desc_discapacidad_mr = fields.Integer(
        string="Descendientes con discapacidad",
        compute="_compute_partner_id_ad_required",
        store=True,
    )
    hijos_y_desc_discapacidad_entero_mr = fields.Integer(
        string="Descendientes con discapacidad, computado de forma entera",
        compute="_compute_partner_id_ad_required",
        store=True,
    )
    hijos_y_desc_discapacidad_33 = fields.Integer(
        string="Hijos y descendientes con discapacidad del 33%",
        compute="_compute_partner_id_ad_required",
        store=True,
    )
    hijos_y_desc_discapacidad_entero_33 = fields.Integer(
        string="Hijos y descendientes con discapacidad del 33%"
        ", computados por entero",
        compute="_compute_partner_id_ad_required",
        store=True,
    )
    hijos_y_desc_discapacidad_66 = fields.Integer(
        string="Hijos y descendientes con discapacidad del 66%",
        compute="_compute_partner_id_ad_required",
        store=True,
    )
    hijos_y_desc_discapacidad_entero_66 = fields.Integer(
        string="Hijos y descendientes con discapacidad del 66%"
        ", computados por entero",
        compute="_compute_partner_id_ad_required",
        store=True,
    )
    ascendientes = fields.Integer(
        string="Ascendientes menores de 75 años",
        compute="_compute_partner_id_ad_required",
        store=True,
    )
    ascendientes_entero = fields.Integer(
        string="Ascendientes menores de 75 años, computados por entero",
        compute="_compute_partner_id_ad_required",
        store=True,
    )
    ascendientes_m75 = fields.Integer(
        string="Ascendientes mayores de 75 años",
        compute="_compute_partner_id_ad_required",
        store=True,
    )
    ascendientes_entero_m75 = fields.Integer(
        string="Ascendientes mayores de 75 años, computados por entero",
        compute="_compute_partner_id_ad_required",
        store=True,
    )
    ascendientes_discapacidad_33 = fields.Integer(
        string="Ascendientes con discapacidad",
        compute="_compute_partner_id_ad_required",
        store=True,
    )
    ascendientes_discapacidad_entero_33 = fields.Integer(
        string="Ascendientes con discapacidad, computados por entero",
        compute="_compute_partner_id_ad_required",
        store=True,
    )
    ascendientes_discapacidad_mr = fields.Integer(
        string="Ascendientes con discapacidad de más del 33%",
        compute="_compute_partner_id_ad_required",
        store=True,
    )
    ascendientes_discapacidad_entero_mr = fields.Integer(
        string="Ascendientes con discapacidad de más del 33%" ", computados por entero",
        compute="_compute_partner_id_ad_required",
        store=True,
    )
    ascendientes_discapacidad_66 = fields.Integer(
        string="Ascendientes con discapacidad de más del 66%",
        compute="_compute_partner_id_ad_required",
        store=True,
    )
    ascendientes_discapacidad_entero_66 = fields.Integer(
        string="Ascendientes con discapacidad de más del 66%" ", computados por entero",
        compute="_compute_partner_id_ad_required",
        store=True,
    )
    computo_primeros_hijos_1 = fields.Integer(
        string="1", compute="_compute_partner_id_ad_required", store=True
    )
    computo_primeros_hijos_2 = fields.Integer(
        string="2", compute="_compute_partner_id_ad_required", store=True
    )
    computo_primeros_hijos_3 = fields.Integer(
        string="3", compute="_compute_partner_id_ad_required", store=True
    )
    ad_required = fields.Integer(compute="_compute_ad_required", store=True)

    @api.depends(
        "partner_vat",
        "a_nacimiento",
        "codigo_provincia",
        "aeat_perception_key_id",
        "partner_id",
    )
    def _compute_partner_record_ok(self):
        """Comprobamos que los campos estén introducidos dependiendo de las
        claves y las subclaves."""
        for record in self:
            record.partner_record_ok = bool(
                record.partner_vat
                and record.codigo_provincia
                and record.aeat_perception_key_id
                and record
            )

    @api.depends("partner_id")
    def _compute_partner_vat(self):
        for item in self.filtered(lambda x: x.partner_id):
            item.partner_vat = item.partner_id._parse_aeat_vat_info()[2]

    @api.depends("partner_id")
    def _compute_codigo_provincia(self):
        for item in self:
            code = SPANISH_STATES.get(item.partner_id.state_id.code)
            item.codigo_provincia = code if code else "98"

    @api.depends("aeat_perception_key_id", "aeat_perception_subkey_id")
    def _compute_ad_required(self):
        for record in self:
            ad_required = record.aeat_perception_key_id.ad_required
            if record.aeat_perception_subkey_id:
                ad_required += record.aeat_perception_subkey_id.ad_required
            record.ad_required = ad_required

    @api.depends("partner_id", "ad_required")
    def _compute_partner_id_ad_required(self):
        """Utilizamos el mismo compute para reducir código al tener la misma lógica."""
        for item in self.filtered(lambda x: x.ad_required >= 2):
            partner = item.partner_id
            item.a_nacimiento = partner.a_nacimiento
            item.discapacidad = partner.discapacidad
            item.movilidad_geografica = partner.movilidad_geografica
            item.representante_legal_vat = partner.representante_legal_vat
            item.situacion_familiar = partner.situacion_familiar
            item.nif_conyuge = partner.nif_conyuge
            item.contrato_o_relacion = partner.contrato_o_relacion
            item.hijos_y_descendientes_m = partner.hijos_y_descendientes_m
            item.hijos_y_descendientes_m_entero = partner.hijos_y_descendientes_m_entero
            item.hijos_y_descendientes = partner.hijos_y_descendientes
            item.hijos_y_descendientes_entero = partner.hijos_y_descendientes_entero
            item.computo_primeros_hijos_1 = partner.computo_primeros_hijos_1
            item.computo_primeros_hijos_2 = partner.computo_primeros_hijos_2
            item.computo_primeros_hijos_3 = partner.computo_primeros_hijos_3
            item.hijos_y_desc_discapacidad_33 = partner.hijos_y_desc_discapacidad_33
            item.hijos_y_desc_discapacidad_entero_33 = (
                partner.hijos_y_desc_discapacidad_entero_33
            )
            item.hijos_y_desc_discapacidad_mr = partner.hijos_y_desc_discapacidad_mr
            item.hijos_y_desc_discapacidad_entero_mr = (
                partner.hijos_y_desc_discapacidad_entero_mr
            )
            item.hijos_y_desc_discapacidad_66 = partner.hijos_y_desc_discapacidad_66
            item.hijos_y_desc_discapacidad_entero_66 = (
                partner.hijos_y_desc_discapacidad_entero_66
            )
            item.ascendientes = partner.ascendientes
            item.ascendientes_entero = partner.ascendientes_entero
            item.ascendientes_m75 = partner.ascendientes_m75
            item.ascendientes_entero_m75 = partner.ascendientes_entero_m75
            item.ascendientes_discapacidad_33 = partner.ascendientes_discapacidad_33
            item.ascendientes_discapacidad_entero_33 = (
                partner.ascendientes_discapacidad_entero_33
            )
            item.ascendientes_discapacidad_mr = partner.ascendientes_discapacidad_mr
            item.ascendientes_discapacidad_entero_mr = (
                partner.ascendientes_discapacidad_entero_mr
            )
            item.ascendientes_discapacidad_66 = partner.ascendientes_discapacidad_66
            item.ascendientes_discapacidad_entero_66 = (
                partner.ascendientes_discapacidad_entero_66
            )

    # Calculo campos SIN incapacidad
    @api.depends("report_id", "report_id.tax_line_ids", "discapacidad")
    def _compute_percepciones_dinerarias(self):
        for item in self.filtered(
            lambda x: not x.discapacidad or x.discapacidad == "0"
        ):
            tax_lines = item.report_id.tax_line_ids.filtered(
                lambda x: x.field_number in (11, 15) and x.res_id == item.report_id.id
            )
            value = 0.0
            for move_line in tax_lines.move_line_ids:
                value += move_line.debit - move_line.credit
            item.percepciones_dinerarias = value

    @api.depends("report_id", "report_id.tax_line_ids", "discapacidad")
    def _compute_retenciones_dinerarias(self):
        for item in self.filtered(
            lambda x: not x.discapacidad or x.discapacidad == "0"
        ):
            tax_lines = item.report_id.tax_line_ids.filtered(
                lambda x: x.field_number in (12, 16) and x.res_id == item.report_id.id
            )
            value = 0.0
            for move_line in tax_lines.move_line_ids:
                value += move_line.credit - move_line.debit
            item.retenciones_dinerarias = value

    @api.depends("report_id", "report_id.tax_line_ids", "discapacidad")
    def _compute_percepciones_en_especie(self):
        for item in self.filtered(
            lambda x: not x.discapacidad or x.discapacidad == "0"
        ):
            tax_lines = item.report_id.tax_line_ids.filtered(
                lambda x: x.field_number == 13 and x.res_id == item.report_id.id
            )
            pde = rde = 0.0
            for move_line in tax_lines.move_line_ids:
                pde += move_line.debit - move_line.credit
                rde += move_line.credit - move_line.debit
            item.percepciones_en_especie = pde - rde

    @api.depends("report_id", "report_id.tax_line_ids", "discapacidad")
    def _compute_ingresos_a_cuenta_efectuados(self):
        for item in self.filtered(
            lambda x: not x.discapacidad or x.discapacidad == "0"
        ):
            tax_lines = item.report_id.tax_line_ids.filtered(
                lambda x: x.field_number == 13 and x.res_id == item.report_id.id
            )
            value = 0.0
            for move_line in tax_lines.move_line_ids:
                value += move_line.debit - move_line.credit
            item.ingresos_a_cuenta_efectuados = value

    @api.depends("report_id", "report_id.tax_line_ids", "discapacidad")
    def _compute_ingresos_a_cuenta_repercutidos(self):
        for item in self.filtered(
            lambda x: not x.discapacidad or x.discapacidad == "0"
        ):
            tax_lines = item.report_id.tax_line_ids.filtered(
                lambda x: x.field_number == 13 and x.res_id == item.report_id.id
            )
            value = 0.0
            for move_line in tax_lines.move_line_ids:
                value += move_line.credit - move_line.debit
            item.ingresos_a_cuenta_repercutidos = value

    # Calculo campos CON incapacidad
    @api.depends("report_id", "report_id.tax_line_ids", "discapacidad")
    def _compute_percepciones_dinerarias_incap(self):
        """La misma lógica que para percepciones_dinerarias."""
        for item in self.filtered(lambda x: x.discapacidad or x.discapacidad != "0"):
            tax_lines = item.report_id.tax_line_ids.filtered(
                lambda x: x.field_number in (11, 15) and x.res_id == item.report_id.id
            )
            value = 0.0
            for move_line in tax_lines.move_line_ids:
                value += move_line.debit - move_line.credit
            item.percepciones_dinerarias_incap = value

    @api.depends("report_id", "report_id.tax_line_ids", "discapacidad")
    def _compute_retenciones_dinerarias_incap(self):
        """La misma lógica que para retenciones_dinerarias."""
        for item in self.filtered(lambda x: x.discapacidad or x.discapacidad != "0"):
            tax_lines = item.report_id.tax_line_ids.filtered(
                lambda x: x.field_number in (12, 16) and x.res_id == item.report_id.id
            )
            value = 0.0
            for move_line in tax_lines.move_line_ids:
                value += move_line.credit - move_line.debit
            item.retenciones_dinerarias_incap = value

    @api.depends("report_id", "report_id.tax_line_ids", "discapacidad")
    def _compute_percepciones_en_especie_incap(self):
        """La misma lógica que para percepciones_en_especie."""
        for item in self.filtered(lambda x: x.discapacidad or x.discapacidad != "0"):
            tax_lines = item.report_id.tax_line_ids.filtered(
                lambda x: x.field_number == 13 and x.res_id == item.report_id.id
            )
            pde = rde = 0.0
            for move_line in tax_lines.move_line_ids:
                pde += move_line.debit - move_line.credit
                rde += move_line.credit - move_line.debit
            item.percepciones_en_especie_incap = pde - rde

    @api.depends("report_id", "report_id.tax_line_ids", "discapacidad")
    def _compute_ingresos_a_cuenta_efectuados_incap(self):
        """La misma lógica que para ingresos_a_cuenta_efectuados."""
        for item in self.filtered(lambda x: x.discapacidad or x.discapacidad != "0"):
            tax_lines = item.report_id.tax_line_ids.filtered(
                lambda x: x.field_number == 13 and x.res_id == item.report_id.id
            )
            value = 0.0
            for move_line in tax_lines.move_line_ids:
                value += move_line.debit - move_line.credit
            item.ingresos_a_cuenta_efectuados_incap = value

    @api.depends("report_id", "report_id.tax_line_ids", "discapacidad")
    def _compute_ingresos_a_cuenta_repercutidos_incap(self):
        """La misma lógica que para ingresos_a_cuenta_repercutidos."""
        for item in self.filtered(lambda x: x.discapacidad or x.discapacidad != "0"):
            tax_lines = item.report_id.tax_line_ids.filtered(
                lambda x: x.field_number == 13 and x.res_id == item.report_id.id
            )
            value = 0.0
            for move_line in tax_lines.move_line_ids:
                value += move_line.credit - move_line.debit
            item.ingresos_a_cuenta_repercutidos_incap = value

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        if self.partner_id:
            if not self.partner_id.state_id:
                raise exceptions.UserError(_("Provincia no definida en el cliente"))
            # Cargamos valores establecidos en el tercero.
            self.aeat_perception_key_id = self.partner_id.aeat_perception_key_id
            self.aeat_perception_subkey_id = self.partner_id.aeat_perception_subkey_id
            if self.aeat_perception_key_id:
                self.aeat_perception_subkey_id = False

    @api.onchange("aeat_perception_key_id")
    def onchange_aeat_perception_key_id(self):
        if self.aeat_perception_key_id:
            self.aeat_perception_subkey_id = False
