# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def sigaus_default_date(self, lines):
        self.ensure_one()
        date = super().sigaus_default_date(lines)
        if not self.invoice_date and lines.mapped("sale_line_ids"):
            date = lines.mapped("sale_line_ids")[0].order_id.date_order.date()
        return date

    @api.model
    def modify_sigaus_line(self, sigaus_line, lines):
        weight = sum(
            line.product_uom_id._compute_quantity(line.quantity, line.product_id.uom_id)
            * line.product_id.weight
            for line in lines
        )
        sigaus_line.write({"quantity": weight})

    def _get_sigaus_line_vals(self, lines=False, **kwargs):
        vals = super()._get_sigaus_line_vals(lines, **kwargs)
        if kwargs.get("sale_sigaus_line"):
            vals["sale_line_ids"] = [kwargs.get("sale_sigaus_line").id]
        return vals

    def manage_sale_sigaus_lines(self):
        sigaus_lines = self.invoice_line_ids.filtered(
            lambda a: a.is_sigaus and a.sale_line_ids
        )
        for sigaus_line in sigaus_lines:
            order_id = sigaus_line.sale_line_ids.order_id[0]
            lines_from_order = self.invoice_line_ids.filtered(
                lambda a: a.sale_line_ids.order_id == order_id
                and a.product_id
                and a.product_id.sigaus_has_amount
            )
            self.modify_sigaus_line(sigaus_line, lines_from_order)
        # In case Sigaus Lines do not exist in the invoice
        # i.e. the line has been deleted in the invoice
        sigaus_lines_in_orders = self.invoice_line_ids.mapped(
            "sale_line_ids.order_id.order_line"
        ).filtered(lambda a: a.is_sigaus)
        not_used_sigaus_lines_in_orders = sigaus_lines_in_orders - sigaus_lines.mapped(
            "sale_line_ids"
        )
        for sigaus_line in not_used_sigaus_lines_in_orders:
            order_id = sigaus_line.order_id
            lines = self.invoice_line_ids.filtered(
                lambda a: a.sale_line_ids.order_id == order_id
                and a.product_id
                and a.product_id.sigaus_has_amount
            )
            if lines:
                self.create_sigaus_line(lines, **{"sale_sigaus_line": sigaus_line})
        sigaus_lines = self.invoice_line_ids.filtered(
            lambda a: a.is_sigaus and a.sale_line_ids
        )
        if len(sigaus_lines) > 1:
            for sigaus_line in sigaus_lines.filtered(
                lambda a: a.sale_line_ids.order_id.name not in a.name
            ):
                sigaus_line.write(
                    {
                        "name": "{}: {}".format(
                            sigaus_line.sale_line_ids.order_id.name,
                            sigaus_line.name,
                        )
                    }
                )

    @api.model
    def get_independent_invoice_lines_domain(self):
        domain = super().get_independent_invoice_lines_domain()
        domain += [("sale_line_ids", "=", False)]
        return domain

    def apply_sigaus(self):
        for rec in self.filtered(
            lambda a: a.is_sigaus
            and a.sigaus_is_date
            and a.move_type in ["out_invoice", "out_refund"]
        ):
            rec.manage_sale_sigaus_lines()
        ret = super().apply_sigaus()
        return ret

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        for move in moves:
            orders = move.line_ids.sale_line_ids.order_id.filtered(
                lambda a: a.is_sigaus
            )
            if orders:
                move.manage_sale_sigaus_lines()
        return moves
