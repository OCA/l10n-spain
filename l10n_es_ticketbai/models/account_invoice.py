# Copyright 2021 Binovo IT Human Project SL
# Copyright 2021 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import datetime
import re
from odoo import models, fields, exceptions, _, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.addons.l10n_es_ticketbai_api.models.ticketbai_invoice import RefundCode, \
    RefundType, SiNoType, TicketBaiInvoiceState
from odoo.addons.l10n_es_ticketbai_api.ticketbai.xml_schema import TicketBaiSchema

INVOICE_NUMBER_RE = re.compile(r'^(.*\D)?(\d*)$')


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    tbai_enabled = fields.Boolean(related='company_id.tbai_enabled', readonly=True)
    tbai_invoice_id = fields.Many2one(
        comodel_name='tbai.invoice', string='TicketBAI Invoice',
        copy=False)
    tbai_invoice_ids = fields.One2many(
        comodel_name='tbai.invoice', inverse_name='invoice_id',
        string='TicketBAI Invoices')
    tbai_cancellation_id = fields.Many2one(
        comodel_name='tbai.invoice',
        string='TicketBAI Cancellation', copy=False)
    tbai_cancellation_ids = fields.One2many(
        comodel_name='tbai.invoice', inverse_name='cancelled_invoice_id',
        string='TicketBAI Cancellations')
    tbai_response_ids = fields.Many2many(
        comodel_name='tbai.response', compute='_compute_tbai_response_ids',
        string='Responses')
    tbai_datetime_invoice = fields.Datetime(
        compute='_compute_tbai_datetime_invoice', store=True, copy=False)
    tbai_date_operation = fields.Datetime('Operation Date', copy=False)
    tbai_description_operation = fields.Text(
        'Operation Description', default="/", copy=False)
    tbai_substitute_simplified_invoice = fields.Boolean(
        'Substitute Simplified Invoice', copy=False)
    tbai_refund_key = fields.Selection(selection=[
        (RefundCode.R1.value, 'Art. 80.1, 80.2, 80.6 and rights founded error'),
        (RefundCode.R2.value, 'Art. 80.3'),
        (RefundCode.R3.value, 'Art. 80.4'),
        (RefundCode.R4.value, 'Art. 80 - other')
    ],
        help="BOE-A-1992-28740. Ley 37/1992, de 28 de diciembre, del Impuesto sobre el "
             "Valor Añadido. Artículo 80. Modificación de la base imponible.",
        copy=False)
    tbai_refund_type = fields.Selection(selection=[
        (RefundType.substitution.value, 'By substitution'),
        (RefundType.differences.value, 'By differences')
    ], copy=False)
    tbai_vat_regime_key = fields.Many2one(
        comodel_name='tbai.vat.regime.key', string='VAT Regime Key', copy=True)
    tbai_vat_regime_key2 = fields.Many2one(
        comodel_name='tbai.vat.regime.key', string='VAT Regime 2nd Key', copy=True)
    tbai_vat_regime_key3 = fields.Many2one(
        comodel_name='tbai.vat.regime.key', string='VAT Regime 3rd Key', copy=True)
    tbai_refund_origin_ids = fields.One2many(
        comodel_name='tbai.invoice.refund.origin',
        inverse_name='account_refund_invoice_id',
        string='TicketBAI Refund Origin References')

    @api.multi
    @api.constrains('state')
    def _check_cancel_number_invoice(self):
        for record in self:
            if record.type in ('out_invoice', 'out_refund') and \
                    record.tbai_enabled and 'draft' == record.state and record.number:
                raise exceptions.ValidationError(_(
                    "Invoice %s. You cannot change to draft a numbered invoice!"
                ) % record.number)

    @api.multi
    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise exceptions.UserError(_(
                    'You cannot delete an invoice which is not draft. '
                    'You should create a credit note instead.'))
        return super().unlink()

    @api.model
    def create(self, vals):
        if vals.get('company_id', False):
            company = self.env['res.company'].browse(vals['company_id'])
        else:
            company = self.env.user.company_id
        if company.tbai_enabled:
            filter_refund = self._context.get('filter_refund', False) \
                or self._context.get('type', False) == 'out_refund'
            invoice_type = vals.get('type', False) \
                or self._context.get('type', False)
            if filter_refund and invoice_type:
                if 'out_refund' == invoice_type:
                    if not vals.get('tbai_refund_type', False):
                        vals['tbai_refund_type'] = RefundType.differences.value
                    if not vals.get('tbai_refund_key', False):
                        vals['tbai_refund_key'] = RefundCode.R1.value
            if vals.get('fiscal_position_id', False):
                fiscal_position = self.env['account.fiscal.position'].browse(
                    vals['fiscal_position_id'])
                vals['tbai_vat_regime_key'] = \
                    fiscal_position.tbai_vat_regime_key.id
                vals['tbai_vat_regime_key2'] = \
                    fiscal_position.tbai_vat_regime_key2.id
                vals['tbai_vat_regime_key3'] = \
                    fiscal_position.tbai_vat_regime_key3.id
        return super().create(vals)

    @api.depends(
        'tbai_invoice_ids', 'tbai_invoice_ids.state',
        'tbai_cancellation_ids', 'tbai_cancellation_ids.state'
    )
    def _compute_tbai_response_ids(self):
        for record in self:
            response_ids = record.tbai_invoice_ids.mapped('tbai_response_ids').ids
            response_ids += record.tbai_cancellation_ids.mapped('tbai_response_ids').ids
            record.tbai_response_ids = [(6, 0, response_ids)]

    @api.depends('date', 'date_invoice')
    def _compute_tbai_datetime_invoice(self):
        for record in self:
            record.tbai_datetime_invoice = fields.Datetime.now()

    @api.onchange('fiscal_position_id')
    def onchange_fiscal_position_id_tbai_vat_regime_key(self):
        if self.fiscal_position_id:
            self.tbai_vat_regime_key = self.fiscal_position_id.tbai_vat_regime_key.id
            self.tbai_vat_regime_key2 = self.fiscal_position_id.tbai_vat_regime_key2.id
            self.tbai_vat_regime_key3 = self.fiscal_position_id.tbai_vat_regime_key3.id

    @api.onchange('tbai_refund_type')
    def onchange_tbai_refund_type(self):
        if self.tbai_refund_type:
            if ('out_invoice' != self.type or
                    ('out_invoice' == self.type and not
                        self.tbai_substitute_simplified_invoice)) and \
                    RefundType.substitution.value == self.tbai_refund_type:
                self.tbai_refund_type = False
                return {
                    'warning': {
                        'title': _("Warning"),
                        'message': _(
                            "TicketBAI refund by substitution is not supported.")
                    }
                }
            elif 'out_refund' != self.type and \
                    RefundType.differences.value == self.tbai_refund_type:
                self.tbai_refund_type = False
                return {
                    'warning': {
                        'title': _("Warning"),
                        'message': _(
                            "TicketBAI refund by differences only available for "
                            "Customer Credit Notes.")
                    }
                }

    @api.onchange('refund_invoice_id')
    def onchange_tbai_refund_invoice_id(self):
        if self.refund_invoice_id:
            if not self.tbai_refund_type:
                self.tbai_refund_type = RefundType.differences.value
            if not self.tbai_refund_key:
                self.tbai_refund_key = RefundCode.R1.value

    def tbai_prepare_invoice_values(self):

        def tbai_prepare_refund_values():
            refunded_inv = self.refund_invoice_id
            if refunded_inv:
                vals.update({
                    'is_invoice_refund': True,
                    'refund_code': self.tbai_refund_key,
                    'refund_type': self.tbai_refund_type,
                    'tbai_invoice_refund_ids': [(0, 0, {
                        'number_prefix': refunded_inv.tbai_get_value_serie_factura(),
                        'number': refunded_inv.tbai_get_value_num_factura(),
                        'expedition_date':
                            refunded_inv.tbai_get_value_fecha_expedicion_factura()
                    })]
                })
            else:
                if self.tbai_refund_origin_ids:
                    refund_id_dicts = []
                    for refund_origin_id in self.tbai_refund_origin_ids:
                        refund_id_dicts.append(
                            (0, 0, {
                                'number_prefix': refund_origin_id.number_prefix,
                                'number': refund_origin_id.number,
                                'expedition_date': refund_origin_id.expedition_date
                            }))
                    vals.update({
                        'is_invoice_refund': True,
                        'refund_code': self.tbai_refund_key,
                        'refund_type': self.tbai_refund_type,
                        'tbai_invoice_refund_ids': refund_id_dicts
                    })

        self.ensure_one()
        partner = self.partner_id
        vals = {
            'invoice_id': self.id,
            'schema': TicketBaiSchema.TicketBai.value,
            'name': self._get_printed_report_name(),
            'company_id': self.company_id.id,
            'number_prefix': self.tbai_get_value_serie_factura(),
            'number': self.tbai_get_value_num_factura(),
            'expedition_date': self.tbai_get_value_fecha_expedicion_factura(),
            'expedition_hour': self.tbai_get_value_hora_expedicion_factura(),
            'simplified_invoice': self.tbai_get_value_simplified_invoice(),
            'substitutes_simplified_invoice':
                self.tbai_get_value_factura_emitida_sustitucion_simplificada(),
            'description': self.tbai_description_operation,
            'amount_total': "%.2f" % self.amount_total_company_signed,
            'vat_regime_key': self.tbai_vat_regime_key.code,
            'vat_regime_key2': self.tbai_vat_regime_key2.code,
            'vat_regime_key3': self.tbai_vat_regime_key3.code
        }
        if partner and not partner.aeat_anonymous_cash_customer:
            vals['tbai_customer_ids'] = [(0, 0, {
                'name': partner.tbai_get_value_apellidos_nombre_razon_social(),
                'country_code': partner.tbai_get_partner_country_code(),
                'nif': partner.tbai_get_value_nif(),
                'identification_number':
                    partner.tbai_partner_identification_number or partner.vat,
                'idtype': partner.tbai_partner_idtype,
                'address': partner.tbai_get_value_direccion(),
                'zip': partner.zip
            })]
        retencion_soportada = self.tbai_get_value_retencion_soportada()
        if retencion_soportada:
            vals['tax_retention_amount_total'] = retencion_soportada
        if self.tbai_is_invoice_refund() and \
                RefundType.differences.value == self.tbai_refund_type:
            tbai_prepare_refund_values()
        operation_date = self.tbai_get_value_fecha_operacion()
        if operation_date:
            vals['operation_date'] = operation_date
        gipuzkoa_tax_agency = self.env.ref(
            "l10n_es_ticketbai_api.tbai_tax_agency_gipuzkoa")
        araba_tax_agency = self.env.ref(
            "l10n_es_ticketbai_api.tbai_tax_agency_araba")
        tax_agency = self.company_id.tbai_tax_agency_id
        if tax_agency in (gipuzkoa_tax_agency, araba_tax_agency):
            lines = []
            for line in self.invoice_line_ids:
                description_line = line.name[:250]
                if self.company_id.tbai_protected_data \
                   and self.company_id.tbai_protected_data_txt:
                    description_line = self.company_id.tbai_protected_data_txt[:250]
                lines.append((0, 0, {
                    'description': description_line,
                    'quantity': line.tbai_get_value_cantidad(),
                    'price_unit': "%.8f" % line.price_unit,
                    'discount_amount': line.tbai_get_value_descuento(),
                    'amount_total': line.tbai_get_value_importe_total()
                }))
            vals['tbai_invoice_line_ids'] = lines
        taxes = []
        tbai_maps = self.env["tbai.tax.map"].search(
            [('code', 'in', ("RE", "IRPF"))]
        )
        exclude_taxes = self.env['l10n.es.aeat.report'].get_taxes_from_templates(
            tbai_maps.mapped("tax_template_ids")
        )
        for tax in self.tax_line_ids.filtered(
                lambda x: x.tax_id not in exclude_taxes):
            tax_subject_to = tax.tax_id.tbai_is_subject_to_tax()
            not_subject_to_cause = \
                not tax_subject_to and tax.tbai_get_value_causa() or ''
            is_exempted = tax_subject_to and tax.tax_id.tbai_is_tax_exempted() or False
            not_exempted_type = tax_subject_to and \
                not is_exempted and tax.tbai_get_value_tipo_no_exenta() or ''
            taxes.append((0, 0, {
                'base': tax.tbai_get_value_base_imponible(),
                'is_subject_to': tax_subject_to,
                'not_subject_to_cause': not_subject_to_cause,
                'is_exempted': is_exempted,
                'exempted_cause': is_exempted and tax.tbai_vat_exemption_key.code or '',
                'not_exempted_type': not_exempted_type,
                'amount': "%.2f" % abs(tax.tax_id.amount),
                'amount_total': tax.tbai_get_value_cuota_impuesto(),
                're_amount': tax.tbai_get_value_tipo_recargo_equivalencia() or '',
                're_amount_total':
                    tax.tbai_get_value_cuota_recargo_equivalencia() or '',
                'surcharge_or_simplified_regime':
                    tax.tbai_get_value_op_recargo_equivalencia_o_reg_simplificado(),
                'type': tax.tbai_get_value_tax_type()
            }))
        vals['tbai_tax_ids'] = taxes
        return vals

    @api.multi
    def _tbai_build_invoice(self):
        for record in self:
            vals = record.tbai_prepare_invoice_values()
            tbai_invoice = record.env['tbai.invoice'].create(vals)
            tbai_invoice.build_tbai_invoice()
            record.tbai_invoice_id = tbai_invoice.id

    def tbai_prepare_cancellation_values(self):
        self.ensure_one()
        vals = {
            'cancelled_invoice_id': self.id,
            'schema': TicketBaiSchema.AnulaTicketBai.value,
            'name': "%s - %s" % (_("Cancellation"), self.number),
            'company_id': self.company_id.id,
            'number_prefix': self.tbai_get_value_serie_factura(),
            'number': self.tbai_get_value_num_factura(),
            'expedition_date': self.tbai_get_value_fecha_expedicion_factura()
        }
        return vals

    @api.multi
    def _tbai_invoice_cancel(self):
        for record in self:
            vals = record.tbai_prepare_cancellation_values()
            tbai_invoice = record.env['tbai.invoice'].create(vals)
            tbai_invoice.build_tbai_invoice()
            record.tbai_cancellation_id = tbai_invoice.id

    @api.multi
    def action_cancel(self):
        non_cancelled_refunds = \
            self.mapped('refund_invoice_ids').filtered(lambda x: 'cancel' != x.state)
        if 0 < len(non_cancelled_refunds):
            raise exceptions.ValidationError(_(
                "You cannot cancel an invoice with non cancelled credit notes.\n"
                "Related invoices: %s") % ', '.join(
                x.number for x in non_cancelled_refunds))
        pending_invoices = self.filtered(
            lambda x: x.tbai_enabled and 'open' == x.state and
            x.tbai_invoice_id and
            TicketBaiInvoiceState.pending.value == x.tbai_invoice_id.state)
        if 0 < len(pending_invoices):
            raise exceptions.ValidationError(_(
                "You cannot cancel an invoice while being sent to the Tax Agency.\n"
                "Related invoices: %s") % ', '.join(x.number for x in pending_invoices))
        tbai_invoices = self.sudo().filtered(
            lambda x: x.tbai_enabled and x.state in ['open', 'in_payment', 'paid'] and
            x.tbai_invoice_id and
            TicketBaiInvoiceState.sent.value == x.tbai_invoice_id.state)
        tbai_invoices._tbai_invoice_cancel()
        return super().action_cancel()

    @api.multi
    def invoice_validate(self):

        def validate_refund_invoices():
            for invoice in refund_invoices:
                valid_refund = True
                error_refund_msg = None
                if not invoice.refund_invoice_id and not invoice.tbai_refund_origin_ids:
                    valid_refund = False
                    error_refund_msg = _("Please, specify data for the original"
                                         " invoices that are going to be refunded")
                if invoice.refund_invoice_id.tbai_invoice_id:
                    valid_refund = invoice.refund_invoice_id.tbai_invoice_id.state in \
                        [
                            TicketBaiInvoiceState.pending.value,
                            TicketBaiInvoiceState.sent.value
                        ]
                    if not valid_refund:
                        error_refund_msg = _(
                            "Some of the original invoices have related tbai invoices "
                            "in inconsistent state please fix them beforehand.")
                if valid_refund and invoice.refund_invoice_id.tbai_cancellation_id:
                    valid_refund = False
                    error_refund_msg = _("Some of the original invoices "
                                         "have related tbai cancelled invoices")
                if not valid_refund:
                    raise exceptions.ValidationError(error_refund_msg)

        res = super().invoice_validate()
        # Credit Notes:
        # A. refund: creates a draft credit note, not validated from wizard.
        # B. cancel: creates a validated credit note from wizard
        # C. modify: creates a validated credit note and a draft invoice.
        #  * The draft invoice won't be a credit note 'by substitution',
        #  but a normal customer invoice.
        # There is no 'by substitution' credit note, only 'by differences'.
        tbai_invoices = self.sudo().env['account.invoice']
        tbai_invoices |= self.sudo().filtered(
            lambda x:
            x.tbai_enabled and 'out_invoice' == x.type and
            x.date and x.date >= x.journal_id.tbai_active_date)
        refund_invoices = \
            self.sudo().filtered(
                lambda x:
                x.tbai_enabled and 'out_refund' == x.type and
                (not x.tbai_refund_type or
                 x.tbai_refund_type == RefundType.differences.value) and
                x.date and x.date >= x.journal_id.tbai_active_date)

        validate_refund_invoices()
        tbai_invoices |= refund_invoices
        tbai_invoices._tbai_build_invoice()
        return res

    @api.model
    def _get_refund_common_fields(self):
        refund_common_fields = super()._get_refund_common_fields()
        refund_common_fields.append('company_id')
        return refund_common_fields

    def _prepare_tax_line_vals(self, line, tax):
        vals = super()._prepare_tax_line_vals(line, tax)
        if self.fiscal_position_id:
            exemption = self.fiscal_position_id.tbai_vat_exemption_ids.filtered(
                lambda e: e.tax_id.id == tax['id'])
            if 1 == len(exemption):
                vals['tbai_vat_exemption_key'] = exemption.tbai_vat_exemption_key.id
        return vals

    def tbai_is_invoice_refund(self):
        if 'out_refund' == self.type or (
                'out_invoice' == self.type and
                RefundType.substitution.value == self.tbai_refund_type):
            res = True
        else:
            res = False
        return res

    def split_invoice_number(self):
        m = re.match(INVOICE_NUMBER_RE, self.number)
        return m.group(1), m.group(2)

    def tbai_get_value_serie_factura(self):
        return self.split_invoice_number()[0]

    def tbai_get_value_num_factura(self):
        return self.split_invoice_number()[1]

    def tbai_get_value_fecha_expedicion_factura(self):
        invoice_date = self.date or self.date_invoice
        date = fields.Datetime.context_timestamp(self, fields.Datetime.from_string(
            invoice_date))
        return date.strftime("%d-%m-%Y")

    def tbai_get_value_hora_expedicion_factura(self):
        invoice_datetime = self.tbai_datetime_invoice
        date = fields.Datetime.context_timestamp(self, fields.Datetime.from_string(
            invoice_datetime))
        return date.strftime("%H:%M:%S")

    def tbai_get_value_simplified_invoice(self):
        if self.partner_id.aeat_anonymous_cash_customer:
            res = SiNoType.S.value
        else:
            res = SiNoType.N.value
        return res

    def tbai_get_value_factura_emitida_sustitucion_simplificada(self):
        if self.tbai_substitute_simplified_invoice:
            res = SiNoType.S.value
        else:
            res = SiNoType.N.value
        return res

    def tbai_get_value_base_rectificada(self):
        return "%.2f" % abs(self.amount_untaxed_signed)

    def tbai_get_value_cuota_rectificada(self):
        amount = abs(self.amount_total_company_signed - self.amount_untaxed_signed)
        return "%.2f" % amount

    def tbai_get_value_fecha_operacion(self):
        if self.tbai_date_operation:
            tbai_date_operation = datetime.strptime(
                self.tbai_date_operation, DEFAULT_SERVER_DATETIME_FORMAT).strftime(
                "%d-%m-%Y")
            date_invoice = datetime.strptime(
                self.date or self.date_invoice, DEFAULT_SERVER_DATE_FORMAT).strftime(
                "%d-%m-%Y")
            if tbai_date_operation == date_invoice:
                tbai_date_operation = None
        else:
            tbai_date_operation = None
        return tbai_date_operation

    def tbai_get_value_retencion_soportada(self):
        tbai_maps = self.env["tbai.tax.map"].search(
            [('code', '=', "IRPF")]
        )
        irpf_taxes = self.env['l10n.es.aeat.report'].get_taxes_from_templates(
            tbai_maps.mapped("tax_template_ids")
        )
        taxes = self.tax_line_ids.filtered(
            lambda tax: tax.tax_id in irpf_taxes)
        if 0 < len(taxes):
            if RefundType.differences.value == self.tbai_refund_type:
                sign = 1
            else:
                sign = -1
            amount_total = sum(
                [tax.tbai_get_amount_total_company() for tax in taxes])
            res = "%.2f" % (sign * amount_total)
        else:
            res = None
        return res


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    def tbai_get_value_cantidad(self):
        if RefundType.differences.value == self.invoice_id.tbai_refund_type:
            sign = -1
        else:
            sign = 1
        return "%.2f" % (sign * self.quantity)

    def tbai_get_value_descuento(self):
        if self.discount:
            if RefundType.differences.value == self.invoice_id.tbai_refund_type:
                sign = -1
            else:
                sign = 1
            res = \
                "%.2f" \
                % \
                (sign * self.quantity * self.price_unit *
                 self.discount / 100.0)
        else:
            res = '0.00'
        return res

    def tbai_get_value_importe_total(self):
        tbai_maps = self.env["tbai.tax.map"].search([('code', '=', "IRPF")])
        irpf_taxes = self.env['l10n.es.aeat.report'].get_taxes_from_templates(
            tbai_maps.mapped("tax_template_ids")
        )
        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = (self.invoice_line_tax_ids - irpf_taxes).compute_all(
            price, currency, self.quantity, product=self.product_id,
            partner=self.invoice_id.partner_id)
        price_total = taxes['total_included'] if taxes else self.price_subtotal
        if RefundType.differences.value == self.invoice_id.tbai_refund_type:
            sign = -1
        else:
            sign = 1
        return "%.2f" % (sign * price_total)
