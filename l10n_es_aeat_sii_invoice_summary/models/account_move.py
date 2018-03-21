# © 2017 FactorLibre - Hugo Santos <hugo.santos@factorlibre.com>
# © 2018 FactorLibre - Victor Rodrigo <victor.rodrigo@factorlibre.com>
# © 2022 ProcessControl - David Ramia <david.ramia@processcontrol.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, api, exceptions, fields, models
from odoo.exceptions import ValidationError
from odoo.fields import Command


class AccountMove(models.Model):
    _inherit = "account.move"

    is_invoice_summary = fields.Boolean("Is SII simplified invoice Summary?")
    sii_invoice_summary_start = fields.Char("SII Invoice Summary: First Invoice")
    sii_invoice_summary_end = fields.Char("SII Invoice Summary: Last Invoice")
    sii_start_date = fields.Date("Start Date")
    sii_end_date = fields.Date("End Date")
    sii_tickets = fields.Text()

    @api.constrains("state")
    def _check_sii_summary(self):
        for invoice in self:
            if invoice.is_invoice_summary and (
                not invoice.sii_invoice_summary_start
                or not invoice.sii_invoice_summary_end
            ):
                raise ValidationError(
                    _("The First invoice and Last invoice fields cannot be empty.")
                )

    def _valid_sii_dates(self):
        if self.sii_start_date and self.sii_end_date:
            if self.sii_start_date > self.sii_end_date:
                raise ValidationError(_("Start date must be before end date."))
        else:
            raise ValidationError(_("Select the start date and end date."))

    def set_order_presented(self, presented=True, order_refs=None):
        if order_refs:
            self.env.cr.execute(
                "UPDATE pos_order SET is_presented=%s WHERE name IN %s",
                (
                    presented,
                    tuple(order_refs),
                ),
            )

    def _populate_invoice_summary_by_dates(self):
        if self.sii_tickets:
            self.set_order_presented(
                presented=False, order_refs=list(self.sii_tickets.split(","))
            )
        pos_order_ids = (
            self.env["pos.order"]
            .with_company(self.company_id)
            .search_read(
                [
                    ("is_presented", "=", False),
                    ("date_order", ">=", self.sii_start_date),
                    ("date_order", "<=", self.sii_end_date),
                ],
                ["id", "name", "amount_total"],
                order="date_order",
            )
        )
        if pos_order_ids:
            order_refs = [pos_order["name"] for pos_order in pos_order_ids]
            self.set_order_presented(order_refs=order_refs)
            self.sii_tickets = ",".join(order_refs)
            self.sii_invoice_summary_start = pos_order_ids[0]["name"]
            self.sii_invoice_summary_end = pos_order_ids[-1]["name"]
            amount_total = sum(
                [pos_order["amount_total"] for pos_order in pos_order_ids]
            )
            sii_line = self.invoice_line_ids.filtered(lambda x: x.is_sii_line)
            if sii_line:
                set_sii_line = [
                    Command.update(
                        sii_line.id,
                        {
                            "price_unit": amount_total,
                        },
                    )
                ]
            else:
                set_sii_line = [
                    Command.create(
                        {
                            "name": "{}-{}".format(
                                self.sii_invoice_summary_start,
                                self.sii_invoice_summary_end,
                            ),
                            "price_unit": amount_total,
                            "is_sii_line": True,
                        }
                    )
                ]
            self.invoice_line_ids = set_sii_line

    def populate_invoice_summary_by_dates(self):
        for invoice in self:
            invoice._valid_sii_dates()
            invoice._populate_invoice_summary_by_dates()

    def action_post(self):
        res = super().action_post()
        for invoice in self:
            if invoice.is_invoice_summary:
                invoice.populate_invoice_summary_by_dates()
        return res

    def _get_aeat_invoice_dict_out(self, cancel=False):
        inv_dict = super()._get_aeat_invoice_dict_out(cancel=cancel)
        if self.is_invoice_summary and self.is_sale_document():
            tipo_factura = "F4"
            if self.sii_invoice_summary_start:
                if self.sii_invoice_summary_start == self.sii_invoice_summary_end:
                    tipo_factura = "F2" if self.move_type == "out_invoice" else "R5"
                else:
                    inv_dict["IDFactura"][
                        "NumSerieFacturaEmisor"
                    ] = self.sii_invoice_summary_start
                    inv_dict["IDFactura"][
                        "NumSerieFacturaEmisorResumenFin"
                    ] = self.sii_invoice_summary_end
            if "FacturaExpedida" in inv_dict:
                if "TipoFactura" in inv_dict["FacturaExpedida"]:
                    inv_dict["FacturaExpedida"]["TipoFactura"] = tipo_factura
                if "Contraparte" in inv_dict["FacturaExpedida"]:
                    del inv_dict["FacturaExpedida"]["Contraparte"]
                if (
                    "TipoRectificativa" in inv_dict["FacturaExpedida"]
                    and tipo_factura == "F4"
                ):
                    del inv_dict["FacturaExpedida"]["TipoRectificativa"]

        return inv_dict

    def _aeat_check_exceptions(self):
        """Inheritable method for exceptions control when sending SII invoices."""
        res = False
        try:
            res = super()._aeat_check_exceptions()
        except exceptions.UserError as e:
            if (
                e.args[0] == _("The partner has not a VAT configured.")
                and self.is_invoice_summary
            ):
                pass
            else:
                raise

        if self.is_invoice_summary and self.is_purchase_document():
            raise exceptions.UserError(_("You can't make a supplier summary invoice."))
        return res

    def write(self, vals):
        """Cannot let change sii_invoice_summary fields
        values in a SII registered supplier invoice"""
        for invoice in self.filtered(
            lambda x: x.is_invoice_summary and x.aeat_state != "not_sent"
        ):
            if "sii_invoice_summary_start" in vals:
                invoice._raise_exception_sii(_("SII Invoice Summary: First Invoice"))
            if "sii_invoice_summary_end" in vals:
                invoice._raise_exception_sii(_("SII Invoice Summary: Last Invoice"))
        return super().write(vals)
