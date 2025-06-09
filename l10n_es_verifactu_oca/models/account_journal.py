# Copyright 2024 Aures TIC - Jose Zambudio <jose@aurestic.es>
# Copyright 2024 Aures TIC - Almudena de La Puente <almudena@aurestic.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    # TODEL?
    # no vamos autilizar el hash de odoo porque la estructura no nos sirve
    # para verifactu, por lo que este código no nos terminaría de valer.
    # De momento lo dejamos hasta saber cómo vamos a controlar
    # el tema de la factura anterior enviada a verifactu para el cálculo
    # del hash, y el control de modificaciones en las facturas ya enviadas.
    restrict_mode_hash_table = fields.Boolean(
        compute="_compute_restrict_mode_hash_table",
        store=True,
        readonly=False,
    )

    restrict_mode_hash_table_readonly = fields.Boolean(
        store=True,
        compute="_compute_restrict_mode_hash_table",
    )

    company_verifactu_enabled = fields.Boolean(
        related="company_id.verifactu_enabled", string="Company veri*FACTU"
    )
    verifactu_enabled = fields.Boolean(string="Enable veri*FACTU", default=True)

    @api.depends(
        "company_id", "company_id.verifactu_enabled", "verifactu_enabled", "type"
    )
    def _compute_restrict_mode_hash_table(self):
        for record in self:
            record.restrict_mode_hash_table_readonly = False
            if (
                record.company_id.verifactu_enabled
                and record.verifactu_enabled
                and record.type == "sale"
            ):
                record.write(
                    {
                        "restrict_mode_hash_table": True,
                        "restrict_mode_hash_table_readonly": True,
                    }
                )

    @api.model
    def check_hash_modification(
        self, verifactu_enabled, journal_type, company_verifactu_enabled
    ):
        if verifactu_enabled and journal_type == "sale" and company_verifactu_enabled:
            raise ValidationError(
                _(
                    "You can't have a sale journal with veri*FACTU enabled"
                    "and not restricted hash modification."
                )
            )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if (
                "restrict_mode_hash_table" in vals
                and not vals["restrict_mode_hash_table"]
            ):
                company = self.env["res.company"].browse(vals.get("company_id"))
                self.check_hash_modification(
                    vals.get("verifactu_enabled"),
                    vals.get("type"),
                    company.verifactu_enabled,
                )
        return super().create(vals_list)

    def write(self, vals):
        if "restrict_mode_hash_table" in vals and not vals["restrict_mode_hash_table"]:
            for record in self:
                new_company_id = vals.get("company_id", record.company_id.id)
                new_company = self.env["res.company"].browse(new_company_id)
                new_type = vals.get("type", record.type)
                new_verifactu_enabled = vals.get(
                    "verifactu_enabled", record.verifactu_enabled
                )
                new_company_verifactu_enabled = new_company.verifactu_enabled
                record.check_hash_modification(
                    new_verifactu_enabled, new_type, new_company_verifactu_enabled
                )
        return super().write(vals)
