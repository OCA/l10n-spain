# Copyright 2021 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMove(models.Model):

    _inherit = "account.move"

    def _recompute_tax_lines(self, recompute_tax_base_amount=False):
        # As we cannot pass the date, we have to use context
        super(
            AccountMove,
            self.with_context(
                vat_prorate_date=self.date or self.invoice_date or fields.Date.today()
            ),
        )._recompute_tax_lines(recompute_tax_base_amount)

    @api.model
    def _get_tax_grouping_key_from_base_line(self, base_line, tax_vals):
        # We need to set the right account. The lines will be marked as 'vat_prorate'
        result = super()._get_tax_grouping_key_from_base_line(base_line, tax_vals)
        if tax_vals.get("vat_prorate", False):
            result["account_id"] = base_line.account_id.id
        result["vat_prorate"] = tax_vals.get("vat_prorate", False)
        return result

    @api.model
    def _get_tax_grouping_key_from_tax_line(self, tax_line):
        result = super()._get_tax_grouping_key_from_tax_line(tax_line)
        result["vat_prorate"] = tax_line.vat_prorate
        return result


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    vat_prorate = fields.Boolean()
