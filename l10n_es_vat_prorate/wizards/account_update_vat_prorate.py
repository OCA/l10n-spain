# Copyright 2025 Tecnativa - Christian Ramos
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.fields import Command


class AccountUpdateVatProrate(models.TransientModel):
    _name = "account.update.vat_prorate"
    _description = "Account Update Vat Prorate"

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    with_vat_prorate = fields.Boolean(
        string="With VAT Prorate",
        help=(
            "If this option is enabled, all invoice lines with VAT " "will be prorated"
        ),
    )
    vat_prorate_ids = fields.One2many(
        "res.company.vat.prorate.wizard",
        inverse_name="wizard_id",
    )
    prorrate_asset_account_id = fields.Many2one(
        "account.account",
        domain="[('company_id', '=', company_id)]",
    )
    prorrate_investment_account_id = fields.Many2one(
        "account.account",
        domain="[('company_id', '=', company_id)]",
    )

    @api.model
    def default_get(self, field_list):
        res = super(AccountUpdateVatProrate, self).default_get(field_list)
        company = self.env.company
        vat_prorate_ids_vals = company.vat_prorate_ids.read(
            [
                "id",
                "company_id",
                "date",
                "type",
                "special_vat_prorate_default",
                "vat_prorate",
            ]
        )
        # Keep track of the original IDs to avoid unlink error if there is any invoice
        # linked to the prorate records
        for vals in vat_prorate_ids_vals:
            vals["origin_vat_prorate_id"] = vals.pop("id")
            vals["company_id"] = vals["company_id"][0] if vals["company_id"] else False
        res.update(
            {
                "company_id": company.id,
                "with_vat_prorate": company.with_vat_prorate,
                "vat_prorate_ids": [Command.clear()]
                + [Command.create(vals) for vals in vat_prorate_ids_vals],
                "prorrate_asset_account_id": (company.prorrate_asset_account_id.id),
                "prorrate_investment_account_id": (
                    company.prorrate_investment_account_id.id
                ),
            }
        )
        return res

    def execute(self):
        self.ensure_one()
        sudo_company = self.company_id.sudo()
        sudo_company.vat_prorate_ids.filtered(
            lambda r: r.id
            not in self.vat_prorate_ids.mapped("origin_vat_prorate_id.id")
        ).unlink()
        for vat_prorate in self.vat_prorate_ids:
            vals = {
                "company_id": sudo_company.id,
                "date": vat_prorate.date,
                "type": vat_prorate.type,
                "vat_prorate": vat_prorate.vat_prorate,
                "special_vat_prorate_default": vat_prorate.special_vat_prorate_default,
            }
            if vat_prorate.origin_vat_prorate_id:
                vals.pop("company_id")
                vat_prorate.origin_vat_prorate_id.write(vals)
            else:
                self.env["res.company.vat.prorate"].create(vals)
        sudo_company.write(
            {
                "with_vat_prorate": self.with_vat_prorate,
                "prorrate_asset_account_id": (self.prorrate_asset_account_id.id),
                "prorrate_investment_account_id": (
                    self.prorrate_investment_account_id.id
                ),
            }
        )


class ResCompanyVatProrate(models.TransientModel):
    _name = "res.company.vat.prorate.wizard"
    _inherit = "res.company.vat.prorate"
    _description = "Res Company Vat Prorate Wizard"

    wizard_id = fields.Many2one(
        comodel_name="account.update.vat_prorate",
    )
    origin_vat_prorate_id = fields.Many2one(
        comodel_name="res.company.vat.prorate",
    )
