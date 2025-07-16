# Copyright 2024 Aures TIC - Almudena de La Puente <almudena@aurestic.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class VerifactuChaining(models.Model):
    _name = "verifactu.chaining"
    _inherit = "mail.thread"
    _description = "Verifactu Chaining"

    name = fields.Char(string="Chaining Name", required=True, tracking=True)
    last_verifactu_invoice_entry_id = fields.Many2one(
        comodel_name="verifactu.invoice.entry",
        string="Last Verifactu Invoice Entry",
        help="Reference to the last verifactu invoice entry for this company. "
        "Used for atomic chaining.",
        copy=False,
        readonly=True,
    )
    sif_id = fields.Char(string="SIF ID", required=True, tracking=True)
    installation_number = fields.Integer(default=1, required=True, tracking=True)

    _sql_constraints = [
        (
            "verifactu_chaining_name_uniq",
            "unique(name)",
            "A Chaining with the same name already exists!",
        )
    ]

    @api.ondelete(at_uninstall=False)
    def _unlink_except_used_chaining(self):
        if self.env["verifactu.invoice.entry"].search(
            [("verifactu_chaining_id", "in", self.ids)], limit=1
        ):
            raise UserError(
                _("You cannot delete a chaining that is in use by an invoice entry.")
            )
