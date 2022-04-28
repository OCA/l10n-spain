# Copyright 2021 Binovo IT Human Project SL
# Copyright 2021 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, exceptions, fields, models

from ..utils import utils as tbai_utils


class TicketBaiInvoiceLine(models.Model):
    _name = "tbai.invoice.line"
    _description = "TicketBAI Invoice details/lines"

    tbai_invoice_id = fields.Many2one(
        comodel_name="tbai.invoice", required=True, ondelete="cascade"
    )
    description = fields.Char(required=True)
    quantity = fields.Char(
        required=True,
        help="String of float with 12 digits and 2 decimal points.",
    )
    price_unit = fields.Char(
        required=True,
        help="String of float with 12 digits and 8 decimal points.",
    )
    discount_amount = fields.Char(
        default="0.00",
        help="String of float with 12 digits and 2 decimal points.",
    )
    amount_total = fields.Char(
        required=True,
        help="String of float with 12 digits and 2 decimal points.",
    )

    @api.constrains("description")
    def _check_description(self):
        for record in self:
            if 250 < len(record.description):
                raise exceptions.ValidationError(
                    _(
                        "TicketBAI Invoice %(name)s:\n"
                        "Description %(desc)s longer than expected. "
                        "Should be 250 characters max.!"
                    )
                    % {"name": record.tbai_invoice_id.name, "desc": record.description}
                )

    @api.constrains("quantity")
    def _check_quantity(self):
        for record in self:
            tbai_utils.check_str_decimal(
                _("TicketBAI Invoice %(name)s: Line %(desc)s Quantity")
                % {"name": record.tbai_invoice_id.name, "desc": record.description},
                record.quantity,
            )

    @api.constrains("price_unit")
    def _check_price_unit(self):
        for record in self:
            tbai_utils.check_str_decimal(
                _("TicketBAI Invoice %(name)s: Line %(desc)s Price Unit")
                % {"name": record.tbai_invoice_id.name, "desc": record.description},
                record.price_unit,
                no_decimal_digits=8,
            )

    @api.constrains("discount_amount")
    def _check_discount_amount(self):
        for record in self:
            if record.discount_amount:
                tbai_utils.check_str_decimal(
                    _("TicketBAI Invoice %(name)s: Line %(desc)s Discount Amount")
                    % {"name": record.tbai_invoice_id.name, "desc": record.description},
                    record.discount_amount,
                )

    @api.constrains("amount_total")
    def _check_amount_total(self):
        for record in self:
            tbai_utils.check_str_decimal(
                _("TicketBAI Invoice %(name)s: Line %(desc)s Amount Total")
                % {"name": record.tbai_invoice_id.name, "desc": record.description},
                record.amount_total,
            )
