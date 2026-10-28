# Copyright 2026 Studio73 - Pablo Cortés <pablo.cortes@studio73.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import api, fields, models


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    l10n_es_bank_id = fields.Many2one(
        comodel_name="l10n.es.bank",
        string="Spanish Bank",
        ondelete="set null",
        index=True,
        copy=False,
    )

    @api.model
    def _get_bank_from_iban(self, account_number):
        values = super()._get_bank_from_iban(account_number)
        country_id = values.get("country_id")
        if not country_id:
            return values
        country = self.env["res.country"].browse(country_id)
        if country.code != "ES":
            return values

        iban = re.sub(r"\W+", "", account_number or "").upper()
        if not iban.startswith("ES") or len(iban) < 8:
            return values

        bank = self.env["l10n.es.bank"].search([("code", "=", iban[4:8])], limit=1)
        if bank:
            values.update(bank._get_partner_bank_values())
            values["l10n_es_bank_id"] = bank.id
        return values

    @api.model
    def _add_bank_vals(self, vals):
        values = super()._add_bank_vals(vals)
        bank = self.env["l10n.es.bank"].browse(values.get("l10n_es_bank_id"))
        if bank.exists():
            for field_name, value in bank._get_partner_bank_values().items():
                values.setdefault(field_name, value)
        return values

    @api.onchange("l10n_es_bank_id")
    def _onchange_l10n_es_bank_id(self):
        for account in self.filtered("l10n_es_bank_id"):
            for (
                field_name,
                value,
            ) in account.l10n_es_bank_id._get_partner_bank_values().items():
                if not account[field_name]:
                    account[field_name] = value
