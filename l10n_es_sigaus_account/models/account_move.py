# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "sigaus.mixin"]

    _sigaus_secondary_unit_fields = {
        "line_ids": "invoice_line_ids",
        "date_field": "invoice_date",
        "editable_states": [
            "draft",
        ],
    }

    @api.depends(
        "company_id",
        "fiscal_position_id",
        "move_type",
        "partner_id",
    )
    def _compute_is_sigaus(self):
        for rec in self:
            if rec.is_invoice():
                return super()._compute_is_sigaus()
            else:
                rec.is_sigaus = False

    @api.depends("is_sigaus", "invoice_date", "company_id")
    def _compute_sigaus_is_date(self):
        ret = super()._compute_sigaus_is_date()
        for rec in self.filtered(
            lambda a: a.is_sigaus
            and not a.invoice_date
            and a.company_id.sigaus_date_from
        ):
            rec.sigaus_is_date = (
                rec.create_date.date() >= rec.company_id.sigaus_date_from
            )
        return ret

    @api.depends("invoice_line_ids")
    def _compute_sigaus_has_line(self):
        return super()._compute_sigaus_has_line()

    @api.depends("company_id")
    def _compute_sigaus_company(self):
        return super()._compute_sigaus_company()

    def sigaus_default_date(self, lines):
        self.ensure_one()
        return self.invoice_date or self.create_date.date()

    @api.model
    def get_independent_invoice_lines_domain(self):
        """
        Override this method to get the invoice lines not related to other
        models (i.e. sale orders)
        """
        return []

    def manage_sigaus_invoice_lines(self):
        for move in self:
            domain = move.get_independent_invoice_lines_domain()
            # Reuse relation instead of search([("move_id","=",move.id)])
            sigaus_lines = move.invoice_line_ids.filtered(lambda line: line.is_sigaus)
            if domain:
                sigaus_lines = sigaus_lines.filtered_domain(domain)
            sigaus_lines.unlink()
            # Invoice lines not related to other documents (i.e. sales)
            product_lines = move.invoice_line_ids.filtered(
                lambda line: line.product_id and line.product_id.sigaus_has_amount
            )
            if domain:
                product_lines = product_lines.filtered_domain(domain)
            if product_lines:
                move.create_sigaus_line(product_lines)

    def create_sigaus_line(self, lines, **kwargs):
        values = self._get_sigaus_line_vals(lines, **kwargs)
        self.env["account.move.line"].create(values)

    def apply_sigaus(self):
        f_invoices = self.filtered(
            lambda a: a.state == "draft" and a.is_sigaus and a.sigaus_is_date and a.id
        )
        f_invoices.automatic_sigaus_exception()
        f_invoices.with_context(avoid_recursion=True).manage_sigaus_invoice_lines()

    def write(self, vals):
        res = super().write(vals)
        if any(
            value in list(vals.keys())
            for value in [
                "is_sigaus",
                "company_id",
                "fiscal_position_id",
                "invoice_line_ids",
                "move_type",
                "invoice_date",
            ]
        ):
            self.with_context(avoid_recursion=True)._delete_sigaus()
            self.apply_sigaus()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        f_moves = moves.filtered(lambda a: a.is_sigaus and a.sigaus_is_date)
        f_moves.automatic_sigaus_exception()
        f_moves.apply_sigaus()
        return moves
