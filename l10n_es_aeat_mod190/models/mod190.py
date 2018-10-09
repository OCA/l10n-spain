
from odoo import api, fields, models, exceptions, _


class L10nEsAeatMod190Report(models.Model):

    _description = 'AEAT 190 report'
    _inherit = 'l10n.es.aeat.report.tax.mapping'
    _name = 'l10n.es.aeat.mod190.report'
    _aeat_number = '190'
    _period_quarterly = False
    _period_monthly = False
    _period_yearly = True

    casilla_01 = fields.Integer(string="[01] Recipients", readonly=True)
    casilla_02 = fields.Float(string="[02] Amount of perceptions")
    casilla_03 = fields.Float(string="[03] Amount of retentions")
    partner_record_ids = fields.One2many(
        comodel_name='l10n.es.aeat.mod190.report.line',
        inverse_name='report_id', string='Partner records', ondelete='cascade')
    registro_manual = fields.Boolean(string='Manual records', default=False)
    calculado = fields.Boolean(string='Calculated', default=False)

    @api.multi
    def _check_report_lines(self):
        """Checks if all the fields of all the report lines
        (partner records) are filled """
        for item in self:
            for partner_record in item.partner_record_ids:
                if not partner_record.partner_record_ok:
                    raise exceptions.UserError(
                        _("All partner records fields (country, VAT number) "
                          "must be filled."))

    @api.multi
    def button_confirm(self):
        for report in self:
            valid = True
            if self.casilla_01 != len(report.partner_record_ids):
                valid = False

            percepciones = 0.0
            retenciones = 0.0
            for line in report.partner_record_ids:
                percepciones += \
                    line.percepciones_dinerarias + \
                    line.percepciones_en_especie + \
                    line.percepciones_dinerarias_incap + \
                    line.percepciones_en_especie_incap

                retenciones += \
                    line.retenciones_dinerarias + \
                    line.retenciones_dinerarias_incap

            if self.casilla_02 != percepciones:
                valid = False

            if self.casilla_03 != retenciones:
                valid = False

            if not valid:
                raise exceptions.UserError(
                    _("You have to recalculate the report before confirm it."))

        return super(L10nEsAeatMod190Report, self).button_confirm()

    @api.multi
    def calculate(self):
        res = super(L10nEsAeatMod190Report, self).calculate()

        for report in self:
            tax_code_map = self.env['l10n.es.aeat.map.tax'].search(
                [('model', '=', report.number),
                 '|',
                 ('date_from', '<=', report.date_start),
                 ('date_from', '=', False),
                 '|',
                 ('date_to', '>=', report.date_end),
                 ('date_to', '=', False)], limit=1)
            if tax_code_map:
                tax_lines = []
                lines = tax_code_map.map_line_ids.search(
                    [('field_number', 'in', (11, 12, 13, 14, 15, 16)),
                     ('map_parent_id', '=', tax_code_map.id)])
                for map_line in lines:
                    tax_lines.append(report._prepare_tax_line_vals(map_line))
            else:
                raise exceptions.UserError(_("No taxes mapped."))

            tax_lines = report.tax_line_ids.filtered(
                lambda x: x.field_number in (
                    11, 12, 13, 14, 15, 16) and x.res_id == report.id)
            if tax_lines:
                for rp in tax_lines.mapped(
                        'move_line_ids').mapped('partner_id'):
                    exist_rp = False
                    for rpr_ids in report.partner_record_ids:
                        if rpr_ids.partner_id.id == rp.id:
                            exist_rp = True
                    if not exist_rp:
                        if rp.state_id.code:
                            aeat_sc_obj = self.env['aeat.state.code.mapping']
                            codigo_provincia = aeat_sc_obj.search(
                                [('state_code', '=',
                                  self.partner_id.state_id.code)]).aeat_code
                        else:
                            exceptions.UserError(
                                _('The state is not defined in the partner, %s'
                                  % rp.name))
                        if not rp.performance_key:
                            raise exceptions.UserError(
                                _("The perception key of the partner, %s. "
                                    "Must be filled." % rp.name))
                        values = {
                            'report_id': report.id,
                            'partner_id': rp.id,
                            'partner_vat': rp.vat,
                            'a_nacimiento': rp.a_nacimiento,
                            'clave_percepcion': rp.performance_key.id,
                            'codigo_provincia': codigo_provincia,
                            'partner_record_ok': True,
                            'discapacidad': rp.discapacidad,
                            'ceuta_melilla': rp.ceuta_melilla,
                            'movilidad_geografica': rp.movilidad_geografica,
                            'representante_legal_vat':
                                rp.representante_legal_vat,
                            'situacion_familiar': rp.situacion_familiar,
                            'nif_conyuge': rp.nif_conyuge,
                            'contrato_o_relacion': rp.contrato_o_relacion,
                            'hijos_y_descendientes_m':
                                rp.hijos_y_descendientes_m,
                            'hijos_y_descendientes_m_entero':
                                rp.hijos_y_descendientes_m_entero,
                            'hijos_y_descendientes':
                                rp.hijos_y_descendientes_m,
                            'hijos_y_descendientes_entero':
                                rp.hijos_y_descendientes_entero,
                            'computo_primeros_hijos_1':
                                rp.computo_primeros_hijos_1,
                            'computo_primeros_hijos_2':
                                rp.computo_primeros_hijos_2,
                            'computo_primeros_hijos_3':
                                rp.computo_primeros_hijos_3,
                            'hijos_y_desc_discapacidad_33':
                                rp.hijos_y_desc_discapacidad_33,
                            'hijos_y_desc_discapacidad_entero_33':
                                rp.hijos_y_desc_discapacidad_entero_33,
                            'hijos_y_desc_discapacidad_mr':
                                rp.hijos_y_desc_discapacidad_mr,
                            'hijos_y_desc_discapacidad_entero_mr':
                                rp.hijos_y_desc_discapacidad_entero_mr,
                            'hijos_y_desc_discapacidad_66':
                                rp.hijos_y_desc_discapacidad_66,
                            'hijos_y_desc_discapacidad_entero_66':
                                rp.hijos_y_desc_discapacidad_entero_66,
                            'ascendientes': rp.ascendientes,
                            'ascendientes_entero': rp.ascendientes_entero,
                            'ascendientes_m75': rp.ascendientes_m75,
                            'ascendientes_entero_m75':
                                rp.ascendientes_entero_m75,
                            'ascendientes_discapacidad_33':
                                rp.ascendientes_discapacidad_33,
                            'ascendientes_discapacidad_entero_33':
                                rp.ascendientes_discapacidad_entero_33,
                            'ascendientes_discapacidad_mr':
                                rp.ascendientes_discapacidad_mr,
                            'ascendientes_discapacidad_entero_mr':
                                rp.ascendientes_discapacidad_entero_mr,
                            'ascendientes_discapacidad_66':
                                rp.ascendientes_discapacidad_66,
                            'ascendientes_discapacidad_entero_66':
                                rp.ascendientes_discapacidad_entero_66,
                        }

                        if not report.registro_manual:
                            pd = 0.0
                            tax_lines = report.tax_line_ids.filtered(
                                lambda x: x.field_number in (
                                    11, 15) and x.res_id == report.id)
                            for t in tax_lines:
                                for m in t.move_line_ids:
                                    if m.partner_id.id == rp.id:
                                        pd += m.debit - m.credit

                            rd = 0.0
                            tax_lines = report.tax_line_ids.filtered(
                                lambda x: x.field_number in (
                                    12, 16) and x.res_id == report.id)
                            for t in tax_lines:
                                for m in t.move_line_ids:
                                    if m.partner_id.id == rp.id:
                                        rd += m.credit - m.debit

                            pde = 0.0
                            tax_lines = \
                                report.tax_line_ids.filtered(
                                    lambda x:
                                    x.field_number == 13 and
                                    x.res_id == report.id)
                            for t in tax_lines:
                                for m in t.move_line_ids:
                                    if m.partner_id.id == rp.id:
                                        pde += m.debit - m.credit

                            rde = 0.0
                            tax_lines = \
                                report.tax_line_ids.filtered(
                                    lambda x:
                                    x.field_number == 14 and
                                    x.res_id == report.id)
                            for t in tax_lines:
                                for m in t.move_line_ids:
                                    if m.partner_id.id == rp.id:
                                        rde += m.credit - m.debit

                            if not rp.discapacidad or rp.discapacidad == '0':
                                values['percepciones_dinerarias'] = pd
                                values['retenciones_dinerarias'] = rd
                                values['percepciones_en_especie'] = pde - rde
                                values['ingresos_a_cuenta_efectuados'] = pde
                                values['ingresos_a_cuenta_repercutidos'] = rde
                            else:
                                values['percepciones_dinerarias_incap'] = pd
                                values['retenciones_dinerarias_incap'] = rd
                                values['percepciones_en_especie_incap'] = \
                                    pde - rde
                                values[
                                    'ingresos_a_cuenta_efectuados_incap'] = \
                                    pde
                                values[
                                    'ingresos_a_cuenta_repercutidos_incap'] = \
                                    rde

                        line_obj = self.env['l10n.es.aeat.mod190.report.line']
                        line_obj.create(values)

                registros = 0
                percepciones = 0.0
                retenciones = 0.0

                if report.registro_manual:
                    for line in report.partner_record_ids:
                        registros += 1
                        percepciones += \
                            line.percepciones_dinerarias + \
                            line.percepciones_en_especie + \
                            line.percepciones_dinerarias_incap + \
                            line.percepciones_en_especie_incap

                        retenciones += \
                            line.retenciones_dinerarias + \
                            line.retenciones_dinerarias_incap

                    report.casilla_01 = registros
                    report.casilla_02 = percepciones
                    report.casilla_03 = retenciones

                else:
                    percepciones = 0.0
                    retenciones = 0.0

                    tax_lines = report.tax_line_ids.search(
                        [('field_number', 'in', (11, 12, 13, 14, 15, 16)),
                         ('model', '=', 'l10n.es.aeat.mod190.report'),
                         ('res_id', '=', report.id)])
                    registros = len(
                        tax_lines.mapped('move_line_ids').mapped(
                            'partner_id'))

                    tax_lines = report.tax_line_ids.search(
                        [('field_number', 'in', (11, 13, 15)),
                         ('model', '=', 'l10n.es.aeat.mod190.report'),
                         ('res_id', '=', report.id)])
                    for t in tax_lines:
                        for m in t.move_line_ids:
                            percepciones += m.debit - m.credit

                    tax_lines = report.tax_line_ids.search(
                        [('field_number', 'in', (12, 14, 16)),
                         ('model', '=', 'l10n.es.aeat.mod190.report'),
                         ('res_id', '=', report.id)])
                    for t in tax_lines:
                        for m in t.move_line_ids:
                            retenciones += m.credit - m.debit

                    report.casilla_01 = registros
                    report.casilla_02 = percepciones
                    report.casilla_03 = retenciones

        report.calculado = True
        return res


class L10nEsAeatMod190ReportLine(models.Model):
    _name = 'l10n.es.aeat.mod190.report.line'

    @api.depends('partner_vat', 'a_nacimiento',
                 'codigo_provincia', 'clave_percepcion', 'partner_id')
    def _compute_partner_record_ok(self):
        """Comprobamos que los campos estén introducidos dependiendo de las
           claves y las subclaves."""

        for record in self:
            record.partner_record_ok = (bool(
                record.partner_vat and record.codigo_provincia and
                record.clave_percepcion and record
            ))

    report_id = fields.Many2one(
        comodel_name='l10n.es.aeat.mod190.report',
        string='AEAT 190 Report ID', ondelete="cascade")
    partner_record_ok = fields.Boolean(
        compute="_compute_partner_record_ok", string='Partner Record OK',
        help='Checked if partner record is OK')
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Partner', required=True)
    partner_vat = fields.Char(string='NIF', size=15)
    representante_legal_vat = fields.Char(
        string="L. R. VAT", size=9)
    clave_percepcion = fields.Many2one(
        comodel_name='l10n.es.aeat.report.perception.key',
        string='Perception key', required=True)
    subclave = fields.Many2one(
        comodel_name='l10n.es.aeat.report.perception.subkey',
        string='Perception subkey')
    ejercicio_devengo = fields.Char(
        string='year', size=4)
    ceuta_melilla = fields.Char(
        string='Ceuta or Melilla', size=1)

    # Percepciones y Retenciones

    percepciones_dinerarias = fields.Float(
        string='Monetary perceptions')
    retenciones_dinerarias = fields.Float(
        string='Money withholdings')
    percepciones_en_especie = fields.Float(
        string='Valuation')
    ingresos_a_cuenta_efectuados = fields.Float(
        string='Income paid on account')
    ingresos_a_cuenta_repercutidos = fields.Float(
        string='Income paid into account')
    percepciones_dinerarias_incap = fields.Float(
        string='Monetary perceptions derived from incapacity for work')
    retenciones_dinerarias_incap = fields.Float(
        string='Monetary withholdings derived from incapacity for work')
    percepciones_en_especie_incap = fields.Float(
        string='Perceptions in kind arising from incapacity for work')
    ingresos_a_cuenta_efectuados_incap = fields.Float(
        string='Income on account in kind made as a result of incapacity '
               'for work')
    ingresos_a_cuenta_repercutidos_incap = fields.Float(
        string='Income to account in kind, repercussions derived from '
               'incapacity for work')

    codigo_provincia = fields.Char(
        string="State ISO code", size=2,
        help='''''')

    # DATOS ADICIONALES (solo en las claves A, B.01, B.03, C, E.01 y E.02).

    a_nacimiento = fields.Char(string='Year of birth', size=4)
    situacion_familiar = fields.Selection(
        selection=[
            ('1', '1 - Single, widowed, divorced or separated with children '
                  'under 18 or incapacitated'),
            ('2', '2 - Married and not legally separated and your spouse has '
                  'no annual income above the amount referred to'),
            ('3', '3 - Other.')],
        string='Family situation')
    nif_conyuge = fields.Char(
        string='VAT of the spouse', size=15)
    discapacidad = fields.Selection([
        ('0',
         '0 - No disability or degree of disability less than 33 percent.'),
        ('1', '1 - Degree of disability greater than 33 percent and less than '
              '66 percent.'),
        ('2', '2 - Degree of disability greater than 33 percent and less than '
              '66 percent, and reduced mobility.'),
        ('3', '3 - Degree of disability equal to or greater than 65%.')],
        string='Disability')

    contrato_o_relacion = fields.Selection([
        ('1', '1 - Contract or relationship of a general nature'),
        ('2', '2 - Contract or ratio less than a year'),
        ('3', '3 - Contract or special employment relationship of a dependent '
              'nature'),
        ('4', '4 - Sporadic relationship of manual workers')],
        string='Contract or relationship', size=1)
    movilidad_geografica = fields.Selection([
        ('0', 'NO'), ('1', 'SI')], string='Geographical mobility')
    reduccion_aplicable = fields.Float(string='Applicable reduction')
    gastos_deducibles = fields.Float(string='Deductible expenses')
    pensiones_compensatorias = fields.Float(string='Compensatory pensions')
    anualidades_por_alimentos = fields.Float(string='Annuities for food')
    prestamos_vh = fields.Selection(
        selection=[
            ('0', "0 - Si en ningún momento del ejercicio ha resultado de "
                  "aplicación la reducción del tipo de retención."),
            ('1', '1 - Si en algún momento del ejercicio ha resultado de '
                  'aplicación la reducción del tipo de retención.')],
        string='Comunicación préstamos vivienda habitual')

    hijos_y_descendientes_m = fields.Integer(string='Under 3 years')
    hijos_y_descendientes_m_entero = fields.Integer(string='Entirely')
    hijos_y_descendientes = fields.Integer(string='Rest')
    hijos_y_descendientes_entero = fields.Integer(string='Entirely')

    hijos_y_desc_discapacidad_mr = fields.Integer(
        string='Descendants')
    hijos_y_desc_discapacidad_entero_mr = fields.Integer(
        string='Descendants, computed entirely')
    hijos_y_desc_discapacidad_33 = fields.Integer(
        string='Descendants')
    hijos_y_desc_discapacidad_entero_33 = fields.Integer(
        string='Descendants, computed entirely')
    hijos_y_desc_discapacidad_66 = fields.Integer(
        string='Descendants')
    hijos_y_desc_discapacidad_entero_66 = fields.Integer(
        string='Descendants, computed entirely')

    ascendientes = fields.Integer(string='Ascendents')
    ascendientes_entero = fields.Integer(
        string='Ascendents, computed entirely')
    ascendientes_m75 = fields.Integer(string='Ascendents')
    ascendientes_entero_m75 = fields.Integer(
        string='Ascendents, computed entirely')

    ascendientes_discapacidad_33 = fields.Integer(
        string='Ascendents')
    ascendientes_discapacidad_entero_33 = fields.Integer(
        string='Ascendents, computed entirely')
    ascendientes_discapacidad_mr = fields.Integer(
        string='Ascendents')
    ascendientes_discapacidad_entero_mr = fields.Integer(
        string='Ascendents, computed entirely')
    ascendientes_discapacidad_66 = fields.Integer(
        string='Ascendents')
    ascendientes_discapacidad_entero_66 = fields.Integer(
        string='Ascendents, computed entirely')
    computo_primeros_hijos_1 = fields.Integer(
        string='1')
    computo_primeros_hijos_2 = fields.Integer(
        string='2')
    computo_primeros_hijos_3 = fields.Integer(
        string='3')

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            if self.partner_id.state_id.code:
                aeat_sc_obj = self.env['aeat.state.code.mapping']
                self.codigo_provincia = aeat_sc_obj.search(
                    [('state_code', '=',
                      self.partner_id.state_id.code)]).aeat_code
            else:
                exceptions.UserError(_('Provincia no definida en el cliente'))

            if not self.codigo_provincia:
                self.codigo_provincia = '98'
            self.partner_vat = self.partner_id.vat

            # Cargamos valores establecidos en el tercero.
            self.clave_percepcion = self.partner_id.performance_key
            self.subclave = self.partner_id.subclave
            self.a_nacimiento = self.partner_id.a_nacimiento
            self.discapacidad = self.partner_id.discapacidad
            self.ceuta_melilla = self.partner_id.ceuta_melilla
            self.movilidad_geografica = self.partner_id.movilidad_geografica
            self.representante_legal_vat = \
                self.partner_id.representante_legal_vat
            self.situacion_familiar = self.partner_id.situacion_familiar
            self.nif_conyuge = self.partner_id.nif_conyuge
            self.contrato_o_relacion = self.partner_id.contrato_o_relacion
            self.hijos_y_descendientes_m = \
                self.partner_id.hijos_y_descendientes_m
            self.hijos_y_descendientes_m_entero = \
                self.partner_id.hijos_y_descendientes_m_entero
            self.hijos_y_descendientes = self.partner_id.hijos_y_descendientes
            self.hijos_y_descendientes_entero = \
                self.partner_id.hijos_y_descendientes_entero
            self.computo_primeros_hijos_1 = \
                self.partner_id.computo_primeros_hijos_1
            self.computo_primeros_hijos_2 = \
                self.partner_id.computo_primeros_hijos_2
            self.computo_primeros_hijos_3 = \
                self.partner_id.computo_primeros_hijos_3
            self.hijos_y_desc_discapacidad_33 = \
                self.partner_id.hijos_y_desc_discapacidad_33
            self.hijos_y_desc_discapacidad_entero_33 = \
                self.partner_id.hijos_y_desc_discapacidad_entero_33
            self.hijos_y_desc_discapacidad_mr = \
                self.partner_id.hijos_y_desc_discapacidad_mr
            self.hijos_y_desc_discapacidad_entero_mr = \
                self.partner_id.hijos_y_desc_discapacidad_entero_mr
            self.hijos_y_desc_discapacidad_66 = \
                self.partner_id.hijos_y_desc_discapacidad_66
            self.hijos_y_desc_discapacidad_entero_66 = \
                self.partner_id.hijos_y_desc_discapacidad_entero_66
            self.ascendientes = self.partner_id.ascendientes
            self.ascendientes_entero = self.partner_id.ascendientes_entero
            self.ascendientes_m75 = self.partner_id.ascendientes_m75
            self.ascendientes_entero_m75 = \
                self.partner_id.ascendientes_entero_m75

            self.ascendientes_discapacidad_33 = \
                self.partner_id.ascendientes_discapacidad_33
            self.ascendientes_discapacidad_entero_33 = \
                self.partner_id.ascendientes_discapacidad_entero_33
            self.ascendientes_discapacidad_mr = \
                self.partner_id.ascendientes_discapacidad_mr
            self.ascendientes_discapacidad_entero_mr = \
                self.partner_id.ascendientes_discapacidad_entero_mr
            self.ascendientes_discapacidad_66 = \
                self.partner_id.ascendientes_discapacidad_66
            self.ascendientes_discapacidad_entero_66 = \
                self.partner_id.ascendientes_discapacidad_entero_66

            if self.clave_percepcion:
                self.subclave = False
                return {'domain': {'subclave': [
                    ('perception_id', '=', self.clave_percepcion.id)]}}
            else:
                return {'domain': {'subclave': []}}
        else:
            self.partner_vat = False
            self.codigo_provincia = False

    @api.onchange('clave_percepcion')
    def onchange_clave_percepcion(self):
        if self.clave_percepcion:
            self.subclave = False
            return {'domain': {'subclave': [
                ('perception_id', '=', self.clave_percepcion.id)]}}
        else:
            return {'domain': {'subclave': []}}


class L10nEsAeatReportPerceptionKey(models.Model):
    _name = 'l10n.es.aeat.report.perception.key'
    _description = 'Clave percepcion'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', size=3, required=True)
    aeat_number = fields.Char(string="Model number", size=3, required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    subkey = fields.One2many(
        comodel_name='l10n.es.aeat.report.perception.subkey',
        inverse_name='perception_id', string='Subkeys',
        ondelete='cascade')
    ad_required = fields.Integer('Aditional data required', default=0)


class L10nEsAeatReportPerceptionSubkey(models.Model):
    _name = 'l10n.es.aeat.report.perception.subkey'
    _description = 'Perception Subkey'

    perception_id = fields.Many2one(
        comodel_name='l10n.es.aeat.report.perception.key',
        string='Perception ID')
    name = fields.Char(string='Name', size=2, required=True)
    aeat_number = fields.Char(string="Model number", size=3, required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    ad_required = fields.Integer('Aditional data required', default=0)
