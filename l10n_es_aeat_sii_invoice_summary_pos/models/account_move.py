# Copyright 2025 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
import ast
import itertools
from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.fields import Command


class AccountMove(models.Model):
    _inherit = "account.move"

    sii_start_date = fields.Date("Start Date")
    sii_end_date = fields.Date("End Date")

    @api.constrains("state")
    def _check_sii_summary(self):
        for invoice in self:
            if (
                invoice.is_invoice_summary
                and invoice.state != "draft"
                and (
                    not invoice.sii_invoice_summary_start
                    or not invoice.sii_invoice_summary_end
                )
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

    def set_order_summary(self, pos_order_ids):
        PosOrder = self.env["pos.order"]
        set_pos_order_ids = PosOrder.with_company(self.company_id).search(
            [
                ("invoice_summary_id.id", "=", self.id),
            ],
        )
        (set_pos_order_ids - pos_order_ids).write({"invoice_summary_id": False})

    def _populate_invoice_summary_by_dates(self):
        PosOrder = self.env["pos.order"]
        pos_order_ids = PosOrder.with_company(self.company_id).search(
            [
                ("state", "not in", ["draft", "cancel"]),
                ("date_order", ">=", self.sii_start_date),
                ("date_order", "<=", self.sii_end_date),
            ],
            order="date_order",
        )

        if pos_order_ids:
            self.set_order_summary(pos_order_ids)
            pos_order_ids.write({"invoice_summary_id": self.id})

            self.sii_invoice_summary_start = pos_order_ids[0].name
            self.sii_invoice_summary_end = pos_order_ids[-1].name

            grouped_taxs = defaultdict(lambda: self.env["pos.order.line"])
            for record in pos_order_ids.mapped("lines"):
                grouped_taxs[record.tax_ids] += record

            line_values = [Command.clear()]
            for tax, pos_order_lines in grouped_taxs.items():
                amount_total = sum(line.price_subtotal for line in pos_order_lines)
                line_values.append(
                    Command.create(
                        {
                            "name": "{}-{}".format(
                                self.sii_invoice_summary_start,
                                self.sii_invoice_summary_end,
                            ),
                            "price_unit": amount_total,
                            "tax_ids": [Command.set(tax.ids)],
                        }
                    )
                )
            self.invoice_line_ids = line_values

    def _get_summary_domain(self):
        return [("invoice_summary_id", "=", self.id)]

    def action_pos_order_summary(self):
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "point_of_sale.action_pos_pos_form"
        )
        if action.get("domain") and isinstance(action["domain"], str):
            action["domain"] = ast.literal_eval(action["domain"].strip() or "[]")
        action["domain"] = list(
            itertools.chain(action["domain"] or [], self._get_summary_domain())
        )
        return action

    def populate_invoice_summary_by_dates(self):
        for invoice in self:
            invoice._valid_sii_dates()
            invoice._populate_invoice_summary_by_dates()
