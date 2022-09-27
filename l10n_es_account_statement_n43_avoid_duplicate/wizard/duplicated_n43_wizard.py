from odoo import fields, models


class DuplicatedN43Wizard(models.TransientModel):
    _name = "duplicated.n43.wizard"

    line_ids = fields.Many2many(
        comodel_name="account.bank.statement.line",
        string="Bank Statement Records",
    )
    statement_id = fields.Many2one(
        comodel_name="account.bank.statement", string="Bank Statement"
    )

    def remove_duplicated_lines(self):
        for line_id in self.line_ids:
            statement_id = line_id.statement_id
            self.env["removed.account.bank.statement.line"].create(
                {
                    "statement_id": statement_id.id,
                    "date": line_id.date,
                    "payment_ref": line_id.payment_ref,
                    "amount": line_id.amount,
                }
            )
            statement_id.balance_start += line_id.amount
            line_id.unlink()
