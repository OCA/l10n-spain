# Copyright 2024 Aures TIC - Jose Zambudio
# Copyright 2024 Aures TIC - Almudena de La Puente
# Copyright 2025 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    # This field from Odoo upstream is converted here to computed writable
    restrict_mode_hash_table = fields.Boolean(
        compute="_compute_restrict_mode_hash_table", store=True, readonly=False
    )
    restrict_mode_hash_table_readonly = fields.Boolean(
        store=True, compute="_compute_restrict_mode_hash_table"
    )
    company_verifactu_enabled = fields.Boolean(
        related="company_id.verifactu_enabled", string="VERI*FACTU company enabled"
    )
    verifactu_enabled = fields.Boolean(string="VERI*FACTU enabled", default=True)

    @api.depends(
        "company_id", "company_id.verifactu_enabled", "verifactu_enabled", "type"
    )  # company_id* triggers aren't launched anyway - see res.company~write method
    def _compute_restrict_mode_hash_table(self):
        self.restrict_mode_hash_table = False
        self.restrict_mode_hash_table_readonly = False
        for record in self:
            if (
                record.company_id.verifactu_enabled
                and record.verifactu_enabled
                and record.type == "sale"
            ):
                record.restrict_mode_hash_table = True
                record.restrict_mode_hash_table_readonly = True

    def check_hash_modification(self, vals):
        verifactu_enabled = vals.get("verifactu_enabled", self.verifactu_enabled)
        company_id = vals.get("company_id", self.company_id.id)
        company = self.env["res.company"].browse(company_id)
        journal_type = vals.get("type", self.type)
        if verifactu_enabled and journal_type == "sale" and company.verifactu_enabled:
            raise ValidationError(
                _(
                    "You can't have a sale journal with VERI*FACTU enabled "
                    "and not restricted hash modification."
                )
            )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("restrict_mode_hash_table") is False:
                self.check_hash_modification(vals)
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("restrict_mode_hash_table") is False:
            for record in self:
                record.check_hash_modification(vals)
        return super().write(vals)
