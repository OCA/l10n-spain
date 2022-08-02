from odoo import api, fields, models


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    actual_balance = fields.Monetary("Balance after last transaction")
    removed_transactions = fields.Html("Removed transactions")

    @api.model
    def create(self, vals):
        res = super().create(vals)
        for line_id in res.line_ids:
            transaction_hash = line_id.transaction_hash
            same_line_id = (
                self.env["account.bank.statement.line"].search(
                    [
                        ("transaction_hash", "=", transaction_hash),
                    ]
                )
                - line_id
            )
            if same_line_id:
                date_string = line_id.date.strftime("%d/%m/%Y")
                payment_ref = line_id.payment_ref
                amount = str(round(line_id.amount, 2))
                removed_line = date_string + " " + payment_ref + " " + amount
                if res.removed_transactions:
                    res.removed_transactions += removed_line + "<br>"
                else:
                    res.removed_transactions = removed_line + "<br>"
                res.balance_start += line_id.amount
                line_id.unlink()
        res.balance_end_real = res.balance_end
        return res


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    transaction_hash = fields.Char("N43 transaction register")

    @api.model
    def create(self, vals):
        transaction_raw_register = vals.pop('transaction_raw_register')
        res = super().create(vals)
        stmt_id = res.statement_id
        if stmt_id.actual_balance:
            start_balance = stmt_id.actual_balance
            stmt_id.actual_balance += res.amount
            end_balance = stmt_id.actual_balance
        else:
            start_balance = stmt_id.balance_start
            stmt_id.actual_balance = stmt_id.balance_start + res.amount
            end_balance = stmt_id.actual_balance
        res.transaction_hash = hash(
            (transaction_raw_register, start_balance, end_balance),
        )
        return res
