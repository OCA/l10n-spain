# Copyright 2021 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from ..utils import utils as tbai_utils
from odoo import models, fields, api, exceptions, _


class TicketBaiInvoiceLine(models.Model):
    _name = 'tbai.invoice.line'
    _description = 'TicketBAI Invoice details/lines'

    tbai_invoice_id = fields.Many2one(
        comodel_name='tbai.invoice', required=True, ondelete='cascade')
    description = fields.Char('Description', required=True)
    quantity = fields.Char(
        'Quantity', required=True,
        help='String of float with 12 digits and 2 decimal points.')
    price_unit = fields.Char(
        'Price Unit', required=True,
        help='String of float with 12 digits and 8 decimal points.')
    discount_amount = fields.Char(
        'Discount Amount', default='0.00',
        help='String of float with 12 digits and 2 decimal points.')
    amount_total = fields.Char(
        'Amount Total', required=True,
        help='String of float with 12 digits and 2 decimal points.')

    @api.multi
    @api.constrains('description')
    def _check_description(self):
        for record in self:
            if 250 < len(record.description):
                raise exceptions.ValidationError(_(
                    "TicketBAI Invoice %s:\n"
                    "Description %s longer than expected. "
                    "Should be 250 characters max.!"
                ) % (record.tbai_invoice_id.name, record.description))

    @api.multi
    @api.constrains('quantity')
    def _check_quantity(self):
        for record in self:
            tbai_utils.check_str_decimal(_(
                "TicketBAI Invoice %s: Line %s Quantity"
            ) % (record.tbai_invoice_id.name, record.description), record.quantity)

    @api.multi
    @api.constrains('price_unit')
    def _check_price_unit(self):
        for record in self:
            tbai_utils.check_str_decimal(
                _("TicketBAI Invoice %s: Line %s Price Unit") % (
                    record.tbai_invoice_id.name, record.description),
                record.price_unit, no_decimal_digits=8)

    @api.multi
    @api.constrains('discount_amount')
    def _check_discount_amount(self):
        for record in self:
            if record.discount_amount:
                tbai_utils.check_str_decimal(
                    _("TicketBAI Invoice %s: Line %s Discount Amount") % (
                        record.tbai_invoice_id.name, record.description),
                    record.discount_amount)

    @api.multi
    @api.constrains('amount_total')
    def _check_amount_total(self):
        for record in self:
            tbai_utils.check_str_decimal(_(
                "TicketBAI Invoice %s: Line %s Amount Total"
            ) % (record.tbai_invoice_id.name, record.description), record.amount_total)
