# Copyright 2015-2020 Tecnativa - Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, exceptions, fields, models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.model
    def line_get_convert(self, line, part):
        """Transfer VAT prorrate percent to journal item."""
        res = super().line_get_convert(line, part)
        if line.get("asset_profile_id"):
            inv_line = self.env["account.invoice.line"].browse(line["invl_id"])
            res["vat_prorrate_percent"] = inv_line.vat_prorrate_percent
        return res


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    vat_prorrate_percent = fields.Float(string="Prorrate perc.", default=100)

    @api.constrains("vat_prorrate_percent")
    def check_vat_prorrate_percent(self):
        for line in self:
            if not (0 < line.vat_prorrate_percent <= 100):
                raise exceptions.ValidationError(
                    _("VAT prorrate percent must be between 0.01 and 100")
                )
