# Copyright 2024 Aures TIC - Almudena de La Puente <almudena@aurestic.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class VerifactuChaining(models.Model):
    _name = "verifactu.chaining"
    _description = "Verifactu Chaining"

    name = fields.Char(string="Chaining Name", required=True)
    last_verifactu_invoice_entry_id = fields.Many2one(
        comodel_name="verifactu.invoice.entry",
        string="Last Verifactu Invoice Entry",
        help="Reference to the last verifactu invoice entry for this company. "
        "Used for atomic chaining.",
        copy=False,
        readonly=True,
    )
    sif_id = fields.Char(string="SIF ID", required=True)
    installation_number = fields.Integer(default=1, required=True)

    _sql_constraints = [
        (
            "verifactu_chaining_name_uniq",
            "unique(name)",
            "A Chaining with the same name already exists!",
        )
    ]
