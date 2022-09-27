import hashlib

from odoo import api, fields, models


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    actual_balance = fields.Monetary("Balance after last transaction")
    removed_transaction_ids = fields.One2many(
        comodel_name="removed.account.bank.statement.line",
        inverse_name="statement_id",
        string="Removed Transactions",
    )
    removed_transactions_count = fields.Integer(
        compute="_compute_removed_transactions_count"
    )

    def _compute_removed_transactions_count(self):
        for account in self:
            account.removed_transactions_count = len(account.removed_transaction_ids)


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    transaction_hash = fields.Char("N43 transaction register")

    @api.model
    def create(self, vals):
        transaction_raw_register = vals.pop("transaction_raw_register")
        res = super().create(vals)
        stmt_id = res.statement_id
        if stmt_id.actual_balance:
            start_balance = stmt_id.actual_balance
            stmt_id.actual_balance += round(res.amount, 2)
            end_balance = round(stmt_id.actual_balance, 2)
        else:
            start_balance = stmt_id.balance_start
            stmt_id.actual_balance = stmt_id.balance_start + round(res.amount, 2)
            end_balance = round(stmt_id.actual_balance, 2)
        to_hash = transaction_raw_register + str(start_balance) + str(end_balance)
        hash = hashlib.sha256()
        hash.update(to_hash.encode())
        res.transaction_hash = hash.hexdigest()
        return res
