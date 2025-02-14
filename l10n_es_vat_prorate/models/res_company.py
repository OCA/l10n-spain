# Copyright 2022 Creu Blanca
# Copyright 2023 Tecnativa Carolina Fernandez
# Copyright 2025 Moduon Team
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    with_vat_prorate = fields.Boolean(
        string="With VAT Prorate",
        help="If this option is enabled, all invoice lines with VAT will be prorated",
    )
    vat_prorate_ids = fields.One2many(
        "res.company.vat.prorate", inverse_name="company_id"
    )
    prorrate_asset_account_id = fields.Many2one(
        "account.account",
        domain="[('company_id', '=', id)]",
        compute="_compute_prorrate_accounts",
        store=True,
        readonly=False,
    )
    prorrate_investment_account_id = fields.Many2one(
        "account.account",
        domain="[('company_id', '=', id)]",
        compute="_compute_prorrate_accounts",
        store=True,
        readonly=False,
    )

    @api.depends("chart_template_id", "with_vat_prorate")
    def _compute_prorrate_accounts(self):
        for record in self:
            if record.with_vat_prorate and record.chart_template_id:
                record.prorrate_asset_account_id = self.env.ref(
                    "l10n_es.%s_account_common_6341" % record.id,
                    raise_if_not_found=False,
                )
                record.prorrate_investment_account_id = self.env.ref(
                    "l10n_es.%s_account_common_6342" % record.id,
                    raise_if_not_found=False,
                )
            else:
                record.prorrate_asset_account_id = False
                record.prorrate_investment_account_id = False

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

    @tools.ormcache(
        "self.id",
        "self.prorrate_asset_account_id.id",
        "self.prorrate_investment_account_id.id",
    )
    def _get_tax_prorrate_account_map(self):
        """Get the account mapping according user type"""
        return {
            "asset_current": self.prorrate_asset_account_id.id,
            "asset_non_current": self.prorrate_asset_account_id.id,
            "asset_fixed": self.prorrate_asset_account_id.id,
            "liability_current": self.prorrate_investment_account_id.id,
            "liability_non_current": self.prorrate_investment_account_id.id,
        }


class ResCompanyVatProrate(models.Model):
    _name = "res.company.vat.prorate"
    _description = "VAT Prorate table"
    _rec_name = "date"
    _order = "date DESC"

    company_id = fields.Many2one("res.company", required=True, ondelete="cascade")
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
    can_reprorate = fields.Selection(
        string="Can re-prorate",
        selection=[("yes", "Yes"), ("partial", "Partial"), ("no", "No")],
        compute="_compute_can_reprorate",
        help="Check if the period can be re-prorated",
        store=False,
    )

    def _compute_can_reprorate(self):
        self.can_reprorate = "no"
        for record in self:
            company = record.company_id
            if company.tax_lock_date and company.tax_lock_date >= record.date:
                continue
            user_fiscal_lock_date = company._get_user_fiscal_lock_date()
            if user_fiscal_lock_date < record.date:
                record.can_reprorate = "yes"
                continue

            next_period = self.search(
                [
                    ("company_id", "=", company.id),
                    ("date", ">", record.date),
                ],
                limit=1,
            )
            if not next_period and record.date < user_fiscal_lock_date:
                record.can_reprorate = "partial"

    def action_recompute_period(self):
        self.ensure_one()
        if self.can_reprorate == "no":
            raise UserError(_("You cannot re-prorate this period"))
        next_vat_prorate_period = self.search(
            [
                ("company_id", "=", self.company_id.id),
                ("date", ">", self.date),
            ],
            limit=1,
            order="date ASC",
        )
        move_domain = [
            ("move_type", "in", ["in_invoice", "in_refund"]),
            ("state", "=", "posted"),
        ]
        if self.can_reprorate == "yes":
            move_domain.append(("date", ">=", self.date))
        else:
            move_domain.append(
                ("date", ">", self.company_id._get_user_fiscal_lock_date())
            )

        if next_vat_prorate_period:
            move_domain.append(("date", "<", next_vat_prorate_period.date))

        unable_to_recompute_moves = self.env["account.move"].browse()
        for move in self.env["account.move"].search(move_domain):
            all_reconciled_lines = move.line_ids._all_reconciled_lines().filtered(
                lambda l: l.matched_debit_ids or l.matched_credit_ids
            )
            # Reset to draft
            try:
                move.button_draft()
            except Exception as ex:
                _logger.warning("Unable to re-prorate %s", move, exc_info=ex)
                unable_to_recompute_moves |= move
                continue
            # Clear and Set taxes
            inv_line_map = {
                inv_line: inv_line.tax_ids.ids for inv_line in move.invoice_line_ids
            }
            move.invoice_line_ids.write({"tax_ids": [(6, 0, [])]})
            for inv_line, tax_ids in inv_line_map.items():
                inv_line.write({"tax_ids": [(6, 0, tax_ids)]})
            move.action_post()
            all_reconciled_lines.filtered(lambda line: not line.reconciled).reconcile()

        if not unable_to_recompute_moves:
            # Everything went fine
            return True

        action = self.env.ref("account.action_move_in_invoice_type").read()[0]
        action["display_name"] = _("Unable to recompute VAT prorate Bills and Refunds")
        action["domain"] = [("id", "in", unable_to_recompute_moves.ids)]
        return action

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
