# Copyright 2025 (APSL - Nagarro) Bernat Obrador
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    facturae_payment_reconciliation_reference = fields.Char(string="Emisor Reference")
    facturae_debit_reconciliation_reference = fields.Char(string="Receptor Reference")
    facturae_factoring_bank_account_id = fields.Many2one(
        "res.partner.bank",
        string="Factoring Bank Account",
        help="Bank account of the factoring entity",
    )
