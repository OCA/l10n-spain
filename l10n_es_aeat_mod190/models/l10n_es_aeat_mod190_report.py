
from odoo import api, fields, models, exceptions, _


class L10nEsAeatMod190Report(models.Model):

    _description = 'AEAT 190 report'
    _inherit = 'l10n.es.aeat.report.tax.mapping'
    _name = 'l10n.es.aeat.mod190.report'
    _aeat_number = '190'
    _period_quarterly = False
    _period_monthly = False
    _period_yearly = True

    casilla_01 = fields.Integer(
        string="[01] Recipients",
        compute='_compute_amount'
    )
    casilla_02 = fields.Float(
        string="[02] Amount of perceptions",
        compute='_compute_amount'
    )
    casilla_03 = fields.Float(
        string="[03] Amount of retentions",
        compute='_compute_amount'
    )
    partner_record_ids = fields.One2many(
        comodel_name='l10n.es.aeat.mod190.report.line',
        inverse_name='report_id', string='Partner records', ondelete='cascade')
    registration_by_hand = fields.Boolean(
        oldname="registro_manual",
        string='Manual records', default=False)
    partner_tree_view = fields.Char(
        compute='_compute_partner_tree_view'
    )

    @api.depends('registration_by_hand')
    def _compute_partner_tree_view(self):
        for record in self:
            view = 'l10n_es_aeat_mod190.' \
                   'view_l10n_es_aeat_mod190_report_line_no_create_tree'
            if record.registration_by_hand:
                view = 'l10n_es_aeat_mod190.' \
                       'view_l10n_es_aeat_mod190_report_line_tree'
            record.partner_tree_view = view

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
        self._check_report_lines()
        return super(L10nEsAeatMod190Report, self).button_confirm()

    @api.multi
    def calculate(self):
        res = super(L10nEsAeatMod190Report, self).calculate()
        for report in self:
            if not report.registration_by_hand:
                report.partner_record_ids.unlink()
            tax_lines = report.tax_line_ids.filtered(
                lambda x: x.field_number in (
                    11, 12, 13, 14, 15, 16) and x.res_id == report.id)
            tax_line_vals = {}
            for tax_line in tax_lines:
                for line in tax_line.move_line_ids:
                    rp = line.partner_id
                    if line.aeat_perception_key_id:
                        key_id = line.aeat_perception_key_id
                        subkey_id = line.aeat_perception_subkey_id
                    else:
                        key_id = rp.aeat_perception_key_id
                        subkey_id = rp.aeat_perception_subkey_id
                    check_existance = False
                    if rp.id not in tax_line_vals:
                        tax_line_vals[rp.id] = {}
                    if key_id.id not in tax_line_vals[rp.id]:
                        tax_line_vals[rp.id][key_id.id] = {}
                    if subkey_id.id not in tax_line_vals[rp.id][key_id.id]:
                        tax_line_vals[rp.id][key_id.id][subkey_id.id] = {}
                        check_existance = True
                    if check_existance:
                        partner_record_id = False
                        for rpr_id in report.partner_record_ids:
                            if (
                                rpr_id.partner_id == rp and
                                key_id == rpr_id.aeat_perception_key_id and
                                subkey_id == rpr_id.aeat_perception_subkey_id
                            ):
                                partner_record_id = rpr_id.id
                                break
                        if not partner_record_id:
                            if not rp.aeat_perception_key_id:
                                raise exceptions.UserError(
                                    _("The perception key of the partner, %s. "
                                        "Must be filled." % rp.name))
                            tax_line_vals[rp.id][key_id.id][
                                subkey_id.id
                            ] = report._get_line_mod190_vals(
                                rp, key_id, subkey_id)
                        else:
                            tax_line_vals[rp.id][key_id.id][subkey_id.id] = False
                    if report.registration_by_hand:
                        continue
                    if tax_line_vals[rp.id][key_id.id][subkey_id.id]:
                        values = tax_line_vals[rp.id][key_id.id][subkey_id.id]
                        pd = 0.0
                        if (
                            tax_line.field_number in (11, 15) and
                            tax_line.res_id == report.id
                        ):
                            pd += line.debit - line.credit
                        rd = 0.0
                        if (
                            tax_line.field_number in (12, 16) and
                            tax_line.res_id == report.id
                        ):
                            rd += line.credit - line.debit
                        pde = 0.0
                        if (
                            tax_line.field_number == 13 and
                            tax_line.res_id == report.id
                        ):
                            pde += line.debit - line.credit
                        rde = 0.0
                        if (
                            tax_line.field_number == 13 and
                            tax_line.res_id == report.id
                        ):
                            rde += line.credit - line.debit
                        if not rp.disability or rp.disability == '0':
                            values['monetary_perception'] += pd
                            values['monetary_withholding'] += rd
                            values['perception_in_kind'] += pde - rde
                            values['input_tax_payment_on_account'] += pde
                            values['output_tax_payment_on_account'] += rde
                        else:
                            values['monetary_perception_incapacity'] += pd
                            values['monetary_withholding_incapacity'] += rd
                            values[
                                'perception_in_kind_incapacity'] += pde - rde
                            values['input_tax_payment_on_account_incapacity'] += pde
                            values[
                                'output_tax_payment_on_account_incapacity'] += rde

            line_obj = self.env['l10n.es.aeat.mod190.report.line']
            registros = 0
            for partner_id in tax_line_vals:
                for key_id in tax_line_vals[partner_id]:
                    for subkey_id in tax_line_vals[partner_id][key_id]:
                        values = tax_line_vals[partner_id][key_id][subkey_id]
                        registros += 1
                        if values:
                            line_obj.create(values)
        return res

    @api.depends(
        'partner_record_ids',
        'partner_record_ids.monetary_perception',
        'partner_record_ids.perception_in_kind',
        'partner_record_ids.monetary_perception_incapacity',
        'partner_record_ids.perception_in_kind_incapacity',
        'partner_record_ids.monetary_withholding',
        'partner_record_ids.monetary_withholding_incapacity',
        'tax_line_ids',

    )
    def _compute_amount(self):
        for report in self:
            registros = 0
            percepciones = 0.0
            retenciones = 0.0
            for line in report.partner_record_ids:
                registros += 1
                percepciones += (
                    line.monetary_perception +
                    line.perception_in_kind +
                    line.monetary_perception_incapacity +
                    line.perception_in_kind_incapacity)
                retenciones += (
                    line.monetary_withholding +
                    line.monetary_withholding_incapacity)
            report.casilla_01 = registros
            report.casilla_02 = percepciones
            report.casilla_03 = retenciones

    def _get_line_mod190_vals(self, rp, key_id, subkey_id):
        state_code = self.SPANISH_STATES.get(
            rp.state_id.code, False)
        if not state_code:
            exceptions.UserError(
                _('The state is not defined in the partner, %s') % rp.name)
        vals = {
            'report_id': self.id,
            'partner_id': rp.id,
            'partner_vat': rp.vat,
            'aeat_perception_key_id': key_id.id,
            'aeat_perception_subkey_id': subkey_id.id,
            'state_code': state_code,
            'ceuta_melilla': rp.ceuta_melilla,
            'partner_record_ok': True,
            'monetary_perception': 0,
            'monetary_withholding': 0,
            'perception_in_kind': 0,
            'input_tax_payment_on_account': 0,
            'output_tax_payment_on_account': 0,
            'monetary_perception_incapacity': 0,
            'monetary_withholding_incapacity': 0,
            'perception_in_kind_incapacity': 0,
            'input_tax_payment_on_account_incapacity': 0,
            'output_tax_payment_on_account_incapacity': 0,
        }
        if key_id.additional_data_required + subkey_id.additional_data_required >= 2:
            vals.update({
                field: rp[field] for field in rp._get_applicable_fields()
            })
        return vals


class L10nEsAeatMod190ReportLine(models.Model):
    _name = 'l10n.es.aeat.mod190.report.line'
    _description = "Line for AEAT report Mod 190"
    _inherit = 'l10n.es.mod190.additional.data.mixin'

    @api.depends('partner_vat', 'birth_year',
                 'state_code', 'aeat_perception_key_id', 'partner_id')
    def _compute_partner_record_ok(self):
        """Comprobamos que los campos estén introducidos dependiendo de las
           claves y las subclaves."""

        for record in self:
            record.partner_record_ok = bool(
                record.partner_vat and record.state_code and
                record.aeat_perception_key_id and record
            )

    report_id = fields.Many2one(
        comodel_name='l10n.es.aeat.mod190.report',
        string='AEAT 190 Report ID', ondelete="cascade")
    partner_record_ok = fields.Boolean(
        compute="_compute_partner_record_ok", string='Partner Record OK',
        help='Checked if partner record is OK')
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Partner', required=True)
    partner_vat = fields.Char(string='VAT', size=15)
    legal_representative_vat = fields.Char(
        oldname="representante_legal_vat",
        string="L. R. VAT", size=9)
    accrual_exercise = fields.Char(
        oldname="ejercicio_devengo",
        string='year', size=4)
    ceuta_melilla = fields.Char(
        string='Ceuta or Melilla', size=1)

    # Perception and withholding

    monetary_perception = fields.Float(oldname="percepciones_dinerarias")
    monetary_withholding = fields.Float(oldname="retenciones_dinerarias ")
    perception_in_kind = fields.Float(oldname="percepciones_en_especie")
    input_tax_payment_on_account = fields.Float(
        oldname="ingresos_a_cuenta_efectuados",
    )
    output_tax_payment_on_account = fields.Float(
        oldname="ingresos_a_cuenta_repercutidos")
    monetary_perception_incapacity = fields.Float(
        oldname='percepciones_dinerarias_incap',
        string='Monetary perceptions derived from incapacity for work')
    monetary_withholding_incapacity = fields.Float(
        oldname='retenciones_dinerarias_incap',
        string='Monetary withholdings derived from incapacity for work')
    perception_in_kind_incapacity = fields.Float(
        oldname='percepciones_en_especie_incap',
        string='Perceptions in kind arising from incapacity for work')
    input_tax_payment_on_account_incapacity = fields.Float(
        oldname="ingresos_a_cuenta_efectuados_incap",
        string='Income on account in kind made as a result of incapacity '
               'for work')
    output_tax_payment_on_account_incapacity = fields.Float(
        oldname="ingresos_a_cuenta_repercutidos_incap",
        string='Income to account in kind, repercussions derived from '
               'incapacity for work')
    state_code = fields.Char(
        oldname="codigo_provincia",
        string="State ISO code", size=2,
        help='''''')
    applicable_reduction = fields.Float(oldname="reduccion_aplicable")
    deductible_expenses = fields.Float(oldname="gastos_deducibles")
    compensatory_pension = fields.Float(oldname='pensiones_compensatorias')
    food_annuities = fields.Float(oldname="anualidades_por_alimentos")
    residence_loan = fields.Selection(
        oldname="prestamos_vh",
        selection=[
            ('0', "0 - Si en ningún momento del ejercicio ha resultado de "
                  "aplicación la reducción del tipo de retención."),
            ('1', '1 - Si en algún momento del ejercicio ha resultado de '
                  'aplicación la reducción del tipo de retención.')],
        string='Comunicación préstamos vivienda habitual')

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if not self.partner_id:
            self.partner_vat = False
            self.state_code = False
            return
        if not self.partner_id.state_id:
            exceptions.UserError(
                _('State not defined on %s') % self.partner_id.display_name)
        self.state_code = self.report_id.SPANISH_STATES.get(
            self.partner_id.state_id.code, "98")
        self.partner_vat = self.partner_id.vat
        self.aeat_perception_key_id = self.partner_id.aeat_perception_key_id
        self.aeat_perception_subkey_id = \
            self.partner_id.aeat_perception_subkey_id
        for field in self._get_applicable_fields():
            self[field] = self.partner_id[field]

        if self.aeat_perception_key_id:
            self.aeat_perception_subkey_id = False
            return {'domain': {'aeat_perception_subkey_id': [
                ('aeat_perception_key_id', '=', self.aeat_perception_key_id.id)]}}
        else:
            return {'domain': {'aeat_perception_subkey_id': []}}
