# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from contextlib import suppress

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.bank_account_number import (
    get_iban_part,
    normalize_account_number,
    validate_iban,
)


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    l10n_es_bank_code = fields.Char(
        string="Bank Entity Code",
        compute="_compute_l10n_es_bank_code",
        store=True,
        index="btree_not_null",
        help="Spanish bank entity code, taken from a valid Spanish IBAN.",
    )

    @api.depends("account_number")
    def _compute_l10n_es_bank_code(self):
        for account in self:
            # The normalization of validate_iban, which also drops underscores
            number = normalize_account_number(account.account_number)
            code = False
            if number[:2].upper() == "ES":
                with suppress(ValidationError):
                    code = get_iban_part(validate_iban(account.env, number), "bank")
            account.l10n_es_bank_code = code
