# Copyright 2026 Studio73 - Pablo Cortés <pablo.cortes@studio73.es>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.bank_account_number import get_iban_part, validate_iban


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    l10n_es_bank_code = fields.Char(
        string="Bank Code",
        compute="_compute_l10n_es_bank_code",
        store=True,
        index=True,
        readonly=True,
    )

    @api.depends("account_number")
    def _compute_l10n_es_bank_code(self) -> None:
        for account in self:
            account.l10n_es_bank_code = False
            if not account.account_number:
                continue
            try:
                iban = validate_iban(account.env, account.account_number)
            except ValidationError:
                continue
            if iban[:2].upper() == "ES":
                account.l10n_es_bank_code = get_iban_part(iban, "bank")
