# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # A leased business premises belongs to the company, not to the customer
    l10n_es_aeat_real_estate_id = fields.Many2one(
        domain="[('company_id', '=', company_id), '|', "
        "('partner_id', '=', partner_id), ('owned_by_company', '=', True)]",
    )
