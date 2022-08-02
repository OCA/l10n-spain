from odoo import api, fields, models


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    actual_balance = fields.Monetary("Balance after last transaction")
    removed_transactions = fields.Html("Removed transactions")

    @api.model
    def create(self, vals):
        res = super().create(vals)
        for line_id in res.line_ids:
            amount = round(line_id.amount, 2)
            raw_line = line_id.transaction_raw_register
            start_balance = round(line_id.start_balance, 2)
            if start_balance == 0:
                start_balance = False
            end_balance = round(line_id.end_balance, 2)
            same_line_id = (
                self.env["account.bank.statement.line"].search(
                    [
                        ("transaction_raw_register", "=", raw_line),
                        ("start_balance", "=", start_balance),
                        ("end_balance", "=", end_balance),
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

    transaction_raw_register = fields.Char("N43 transaction register")
    start_balance = fields.Monetary("Balance before transaction")
    end_balance = fields.Monetary("Balance after transaction")

    @api.model
    def create(self, vals):
        res = super().create(vals)
        stmt_id = res.statement_id
        if stmt_id.actual_balance:
            res.start_balance = stmt_id.actual_balance
            stmt_id.actual_balance += res.amount
            res.end_balance = stmt_id.actual_balance
        else:
            res.start_balance = stmt_id.balance_start
            stmt_id.actual_balance = stmt_id.balance_start + res.amount
            res.end_balance = stmt_id.actual_balance
        return res
