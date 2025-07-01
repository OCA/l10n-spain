# Copyright 2024 Jose Zambudio <jose@aurestic.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    verifactu_enabled = fields.Boolean(string="Enable veri*FACTU")
    verifactu_test = fields.Boolean(string="Is it the veri*FACTU test environment?")
    verifactu_description = fields.Text(
        default="/",
        size=500,
        help="The description for Verifactu invoices if not set",
    )
    verifactu_developer_id = fields.Many2one(
        comodel_name="verifactu.developer",
        string="Verifactu Developer",
        ondelete="set null",
    )
    verifactu_start_date = fields.Date(
        help="If this field is set, the verifactu won't be enabled on invoices with lower "
        "invoice date. If not set, the verifactu can be enabled on all invoice dates"
    )
    last_verifactu_invoice_entry_id = fields.Many2one(
        comodel_name="verifactu.invoice",
        string="Last Verifactu Invoice Entry",
        help="Reference to the last verifactu invoice entry for this company. "
        "Used for atomic chaining.",
        copy=False,
    )

    def write(self, vals):
        res = super().write(vals)
        if "verifactu_enabled" in vals:
            for company in self:
                if vals.get("verifactu_enabled", False):
                    journals = self.env["account.journal"].search(
                        [
                            ("company_id", "=", company.id),
                            ("type", "=", "sale"),
                        ]
                    )
                    if journals:
                        journals.write({"verifactu_enabled": True})
        return res
