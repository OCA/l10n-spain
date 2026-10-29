# Copyright 2024 Aures TIC - Jose Zambudio
# Copyright 2025 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    verifactu_enabled = fields.Boolean(string="VERI*FACTU enabled", tracking=True)
    verifactu_test = fields.Boolean(
        string="VERI*FACTU test environment?", tracking=True
    )
    verifactu_description = fields.Text(
        string="VERI*FACTU description",
        default="/",
        help="The description for VERI*FACTU invoices if not set",
        tracking=True,
    )
    verifactu_developer_id = fields.Many2one(
        comodel_name="verifactu.developer",
        string="VERI*FACTU developer",
        ondelete="restrict",
        tracking=True,
    )
    verifactu_start_date = fields.Date(
        string="VERI*FACTU start date",
        help="If this field is set, the VERI*FACTU won't be enabled on invoices with "
        "lower invoice date. If not set, it can be enabled on all invoice dates",
        tracking=True,
    )
    verifactu_chaining_id = fields.Many2one(
        comodel_name="verifactu.chaining",
        string="VERI*FACTU chaining",
        ondelete="restrict",
        tracking=True,
    )

    def write(self, vals):
        # As the compute is not triggered automatically, we need to manually trigger it
        # rewriting the flag at journal level.
        res = super().write(vals)
        if vals.get("verifactu_enabled"):
            self.env["account.journal"].search(
                [("company_id", "in", self.ids), ("type", "=", "sale")]
            ).verifactu_enabled = True
        return res
