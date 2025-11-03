# Copyright 2024 Aures TIC - Almudena de La Puente <almudena@aurestic.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class VerifactuChaining(models.Model):
    _name = "verifactu.chaining"
    _inherit = "mail.thread"
    _description = "VERI*FACTU chaining"

    name = fields.Char(required=True, tracking=True)
    last_verifactu_invoice_entry_id = fields.Many2one(
        comodel_name="verifactu.invoice.entry",
        string="Last invoice entry",
        help="Reference to the last VERI*FACTU invoice entry for this company. "
        "Used for atomic chaining.",
        copy=False,
        readonly=True,
    )
    sif_id = fields.Char(
        string="SIF ID",
        required=True,
        tracking=True,
        size=2,
        help="Identifier of the billing software (SIF). "
        "Must be exactly 2 alphanumeric characters (A,Z, 0,9).",
    )
    installation_number = fields.Integer(default=1, required=True, tracking=True)

    _sql_constraints = [
        (
            "verifactu_chaining_name_uniq",
            "unique(name)",
            "A chaining with the same name already exists!",
        )
    ]
