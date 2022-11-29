# Copyright 2021 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.addons.l10n_es_ticketbai_api.ticketbai.xml_schema import TicketBaiSchema
from odoo.addons.l10n_es_ticketbai_api.models.ticketbai_invoice import \
    TicketBaiInvoiceState, SiNoType
from odoo.addons.l10n_es_ticketbai_api.models.ticketbai_invoice_tax import \
    NotExemptedType
from odoo import models, fields, api, exceptions, _


class PosOrder(models.Model):
    _inherit = 'pos.order'

    tbai_enabled = fields.Boolean(related='company_id.tbai_enabled', readonly=True)
    tbai_invoice_id = fields.Many2one(
        comodel_name='tbai.invoice', string='TicketBAI PoS Order', copy=False)
    tbai_invoice_ids = fields.One2many(
        comodel_name='tbai.invoice', inverse_name='pos_order_id',
        string='TicketBAI Invoices')
    tbai_response_ids = fields.Many2many(
        comodel_name='tbai.response', compute='_compute_tbai_response_ids',
        string='Responses')
    tbai_vat_regime_key = fields.Many2one(
        comodel_name='tbai.vat.regime.key', string='VAT Regime Key', copy=True)

    @api.depends('tbai_invoice_ids', 'tbai_invoice_ids.state')
    def _compute_tbai_response_ids(self):
        for record in self:
            record.tbai_response_ids = [
                (6, 0, record.tbai_invoice_ids.mapped('tbai_response_ids').ids)]

    @api.model
    def _order_fields(self, ui_order):
        res = super()._order_fields(ui_order)
        session = self.env['pos.session'].browse(ui_order['pos_session_id'])
        if session.config_id.tbai_enabled and not ui_order.get('to_invoice', False):
            res['tbai_vat_regime_key'] = ui_order['tbai_vat_regime_key']
        return res

    def tbai_prepare_invoice_values(self, pos_order=None):
        self.ensure_one()
        partner = self.partner_id
        prefix = self.tbai_get_value_serie_factura()
        number = self.tbai_get_value_num_factura()
        expedition_date = self.tbai_get_value_fecha_expedicion_factura()
        expedition_hour = self.tbai_get_value_hora_expedicion_factura()
        vals = {
            'schema': TicketBaiSchema.TicketBai.value,
            'company_id': self.company_id.id,
            'simplified_invoice': SiNoType.S.value,
            'pos_order_id': self.id,
            'name': self.pos_reference,
            'number_prefix': prefix,
            'number': number,
            'expedition_date': expedition_date,
            'expedition_hour': expedition_hour,
            'description': '/',
            'amount_total': "%.2f" % self.amount_total,
            'vat_regime_key': self.tbai_vat_regime_key.code,
            'state': TicketBaiInvoiceState.pending.value
        }
        if partner:
            vals['tbai_customer_ids'] = [(0, 0, {
                'name': partner.tbai_get_value_apellidos_nombre_razon_social(),
                'country_code': partner._parse_aeat_vat_info()[0],
                'nif': partner.tbai_get_value_nif(),
                'identification_number':
                    partner.tbai_partner_identification_number or partner.vat,
                'idtype': partner.tbai_partner_idtype,
                'address': partner.tbai_get_value_direccion(),
                'zip': partner.zip
            })]
        if pos_order is None:
            vals['previous_tbai_invoice_id'] = self.config_id.tbai_last_invoice_id.id
        else:
            previous_order_pos_reference = \
                pos_order.get('tbai_previous_order_pos_reference', False)
            if previous_order_pos_reference:
                tbai_previous_order = self.search([
                    ('pos_reference', '=', previous_order_pos_reference)])
                vals['previous_tbai_invoice_id'] = \
                    tbai_previous_order.tbai_invoice_id.id
            datas = base64.b64encode(pos_order['tbai_datas'].encode('utf-8'))
            vals.update({
                'datas': datas,
                'datas_fname': "%s.xsig" % self.pos_reference.replace('/', '-'),
                'file_size': len(datas),
                'signature_value': pos_order['tbai_signature_value']
            })
        gipuzkoa_tax_agency = self.env.ref(
            "l10n_es_ticketbai_api.tbai_tax_agency_gipuzkoa")
        araba_tax_agency = self.env.ref(
            "l10n_es_ticketbai_api.tbai_tax_agency_araba")
        tax_agency = self.company_id.tbai_tax_agency_id
        is_gipuzkoa_tax_agency = tax_agency == gipuzkoa_tax_agency
        is_araba_tax_agency = tax_agency == araba_tax_agency
        taxes = {}
        lines = []
        for line in self.lines:
            for tax in line.tax_ids_after_fiscal_position:
                taxes.setdefault(tax.id, {
                    'is_subject_to': True, 'is_exempted': False,
                    'not_exempted_type': NotExemptedType.S1.value,
                    'base': 0.0, 'amount': tax.amount, 'amount_total': 0.0
                })
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                computed_tax = tax.compute_all(
                    price, self.pricelist_id.currency_id, line.qty,
                    product=line.product_id, partner=partner)
                amount_total = \
                    computed_tax['total_included'] - computed_tax['total_excluded']
                taxes[tax.id]['base'] += computed_tax['total_excluded']
                taxes[tax.id]['amount_total'] += amount_total
            if is_gipuzkoa_tax_agency or is_araba_tax_agency:
                lines.append((0, 0, {
                    'description': line.name,
                    'quantity': "%.2f" % line.qty,
                    'price_unit': "%.8f" % line.price_unit,
                    'discount_amount':
                        "%.2f" % (line.qty * line.price_unit * line.discount / 100.0),
                    'amount_total': "%.2f" % line.price_subtotal_incl
                }))
        vals['tbai_tax_ids'] = []
        for tax_id, tax_values in taxes.items():
            tax_values['base'] = "%.2f" % tax_values['base']
            tax_values['amount'] = "%.2f" % tax_values['amount']
            tax_values['amount_total'] = "%.2f" % tax_values['amount_total']
            vals['tbai_tax_ids'].append((0, 0, tax_values))
        if is_gipuzkoa_tax_agency or is_araba_tax_agency:
            vals['tbai_invoice_line_ids'] = lines
        return vals

    @api.multi
    def _tbai_build_invoice(self):
        for record in self:
            vals = record.tbai_prepare_invoice_values()
            tbai_invoice = self.env['tbai.invoice'].create(vals)
            tbai_invoice.build_tbai_simplified_invoice()
            record.tbai_invoice_id = tbai_invoice.id

    @api.model
    def _process_order(self, pos_order):
        order = super()._process_order(pos_order)
        if order.config_id.tbai_enabled and not pos_order.get('to_invoice', False):
            vals = order.tbai_prepare_invoice_values(pos_order)
            order.tbai_invoice_id = self.env['tbai.invoice'].sudo().create(vals)
            order.config_id.tbai_last_invoice_id = order.tbai_invoice_id
        return order

    @api.multi
    def _prepare_done_order_for_pos(self):
        res = super()._prepare_done_order_for_pos()
        if self.tbai_enabled and self.tbai_invoice_id:
            res.update({
                'tbai_identifier': self.tbai_invoice_id.tbai_identifier,
                'tbai_qr_src': 'data:image/png;base64,' + str(
                    self.tbai_invoice_id.qr.decode('UTF-8')),
                'tbai_qr_url': self.tbai_invoice_id.qr_url
            })
        return res

    def _prepare_invoice(self):
        res = super(PosOrder, self)._prepare_invoice()
        if self.tbai_enabled:
            vat_regime_key_id = False
            if self.tbai_vat_regime_key:
                vat_regime_key_id = self.tbai_vat_regime_key.id
            elif self.fiscal_position_id:
                vat_regime_key_id = self.fiscal_position_id.tbai_vat_regime_key.id
            elif self.partner_id:
                fp_id = self.env['account.fiscal.position'].get_fiscal_position(
                    self.partner_id.id)
                fp = self.env['account.fiscal.position'].browse(fp_id)
                vat_regime_key_id = fp.tbai_vat_regime_key.id
            if not vat_regime_key_id:
                vat_regime_key_id = \
                    self.env.ref('l10n_es_ticketbai.tbai_vat_regime_01').id
            res.update({
                'tbai_vat_regime_key': vat_regime_key_id
            })
            if self.tbai_invoice_id:
                res.update({
                    'tbai_substitute_simplified_invoice': True,
                    'tbai_substitution_pos_order_id': self.id
                })
        return res

    def tbai_get_value_serie_factura(self):
        sequence = self.config_id.l10n_es_simplified_invoice_sequence_id
        date = fields.Datetime.context_timestamp(
            self, fields.Datetime.from_string(self.date_order)
        ).strftime(DEFAULT_SERVER_DATE_FORMAT)
        prefix, suffix = sequence.with_context(
            ir_sequence_date=date, ir_sequence_date_range=date)._get_prefix_suffix()
        return prefix

    def tbai_get_value_num_factura(self):
        invoice_number_prefix = self.tbai_get_value_serie_factura()
        if invoice_number_prefix and not \
                self.pos_reference.startswith(invoice_number_prefix):
            raise exceptions.ValidationError(_(
                "Simplified Invoice Number Prefix %s is not part of Number %s!"
            ) % (invoice_number_prefix, self.pos_reference))
        return self.pos_reference[len(invoice_number_prefix):]

    def tbai_get_value_fecha_expedicion_factura(self):
        date = fields.Datetime.context_timestamp(
            self, fields.Datetime.from_string(self.date_order))
        return date.strftime("%d-%m-%Y")

    def tbai_get_value_hora_expedicion_factura(self):
        date = fields.Datetime.context_timestamp(
            self, fields.Datetime.from_string(self.date_order))
        return date.strftime("%H:%M:%S")
