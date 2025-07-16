# Copyright 2022 Creu Blanca
# Copyright 2023 Tecnativa Carolina Fernandez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import ormcache

from .prorate_taxes import PRORATE_TAXES


class ResCompany(models.Model):
    _inherit = "res.company"

    with_vat_prorate = fields.Boolean(
        string="With VAT Prorate",
        help="If this option is enabled, all invoice lines with VAT will be prorated",
    )
    vat_prorate_ids = fields.One2many(
        "res.company.vat.prorate", inverse_name="company_id"
    )

    @ormcache("self")
    def _get_prorate_accounts(self):
        prorate_taxes_mapping = {}
        for tax_tmpl in PRORATE_TAXES:
            if PRORATE_TAXES.get(tax_tmpl).get("prorate_account_template_ids"):
                prorate_account_ids = []
                vals = PRORATE_TAXES.get(tax_tmpl)
                for account_tmpl in vals.get("prorate_account_template_ids"):
                    account_from_tmpl_id = self._get_account_id_from_xmlid(account_tmpl)
                    if account_from_tmpl_id:
                        prorate_account_ids.append(account_from_tmpl_id)
                prorate_taxes_mapping[tax_tmpl] = {
                    "prorate_account_ids": prorate_account_ids,
                }
        return prorate_taxes_mapping

    def get_prorate(self, date):
        self.ensure_one()
        return self.env["res.company.vat.prorate"].search(
            [("company_id", "=", self.id), ("date", "<=", date)],
            order="date DESC",
            limit=1,
        )

    @api.constrains("with_vat_prorate", "vat_prorate_ids")
    def _check_vat_prorate_ids(self):
        for rec in self.sudo():
            if rec.with_vat_prorate and not rec.vat_prorate_ids:
                raise ValidationError(_("You must complete VAT prorate information"))


class ResCompanyVatProrate(models.Model):
    _name = "res.company.vat.prorate"
    _description = "VAT Prorate table"
    _rec_name = "date"
    _order = "date DESC"

    company_id = fields.Many2one("res.company", required=True)
    date = fields.Date(required=True, default=fields.Date.today())
    type = fields.Selection(
        selection=[("general", "General"), ("special", "Special")],
        required=True,
        default="general",
        help="If the special prorate is enabled, you will be able to select which "
        "invoice lines will be prorated.",
    )
    special_vat_prorate_default = fields.Boolean(
        string="Special VAT Prorate Default",
        help="If the Special VAT Prorate is enabled, this value indicates "
        "whether all the invoice lines will be prorated by default",
    )
    vat_prorate = fields.Float()

    _sql_constraints = [
        (
            "vat_prorate_percent_amount",
            "CHECK (vat_prorate > 0 and vat_prorate <= 100)",
            "VAT prorate must be between 0.01 and 100!",
        ),
    ]

    @api.constrains("type", "vat_prorate")
    def _check_vat_with_special_prorate_percent(self):
        for rec in self.sudo():
            if rec.type == "special" and rec.vat_prorate == 100:
                raise ValidationError(
                    _("You can't have a special VAT prorrate of 100%")
                )
