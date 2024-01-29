# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def sigaus_default_date(self, lines):
        self.ensure_one()
        date = super().sigaus_default_date(lines)
        if not self.invoice_date and lines.mapped("purchase_order_id"):
            date = lines.mapped("purchase_order_id")[0].date_order.date()
        return date

    def _get_sigaus_line_vals(self, lines=False, **kwargs):
        vals = super()._get_sigaus_line_vals(lines, **kwargs)
        if kwargs.get("purchase_sigaus_line"):
            vals["purchase_line_id"] = kwargs.get("purchase_sigaus_line").id
        return vals

    @api.model
    def modify_sigaus_line(self, sigaus_line, lines):
        weight = sum(
            line.product_uom_id._compute_quantity(line.quantity, line.product_id.uom_id)
            * line.product_id.weight
            for line in lines
        )
        sigaus_line.write({"quantity": weight})

    def manage_purchase_sigaus_lines(self, line_type=None):
        sigaus_lines = self.invoice_line_ids.filtered(
            lambda a: a.is_sigaus and a.purchase_order_id
        )
        for sigaus_line in sigaus_lines:
            order_id = sigaus_line.purchase_order_id
            lines_from_order = self.invoice_line_ids.filtered(
                lambda a: a.purchase_order_id == order_id
                and a.product_id
                and a.product_id.sigaus_has_amount
            )
            self.modify_sigaus_line(sigaus_line, lines_from_order)
        # In case Sigaus Lines do not exist in the invoice
        # i.e. the line has been deleted in the invoice
        sigaus_lines_in_orders = self.invoice_line_ids.mapped(
            "purchase_line_id.order_id.order_line"
        ).filtered(lambda a: a.is_sigaus)
        not_used_sigaus_lines_in_orders = sigaus_lines_in_orders - sigaus_lines.mapped(
            "purchase_line_id"
        )
        for sigaus_line in not_used_sigaus_lines_in_orders:
            order_id = sigaus_line.order_id
            lines = self.invoice_line_ids.filtered(
                lambda a: a.purchase_order_id == order_id
                and a.product_id
                and a.product_id.sigaus_has_amount
            )
            if lines:
                self.create_sigaus_line(lines, **{"purchase_sigaus_line": sigaus_line})
        sigaus_lines = self.invoice_line_ids.filtered(
            lambda a: a.is_sigaus and a.purchase_order_id
        )
        if len(sigaus_lines) > 1:
            for sigaus_line in sigaus_lines.filtered(
                lambda a: a.purchase_order_id.name not in a.name
            ):
                sigaus_line.write(
                    {
                        "name": "{}: {}".format(
                            sigaus_line.purchase_order_id.name,
                            sigaus_line.name,
                        )
                    }
                )

    @api.model
    def get_independent_invoice_lines_domain(self):
        domain = super().get_independent_invoice_lines_domain()
        domain += [("purchase_line_id", "=", False)]
        return domain

    def apply_sigaus(self):
        for rec in self.filtered(
            lambda a: a.is_sigaus
            and a.sigaus_is_date
            and a.move_type in ["in_invoice", "in_refund"]
        ):
            rec.manage_purchase_sigaus_lines()
        ret = super().apply_sigaus()
        return ret

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        if self.env.context.get("from_purchase"):
            moves.filtered(lambda a: a.is_sigaus).manage_purchase_sigaus_lines()
        return moves
