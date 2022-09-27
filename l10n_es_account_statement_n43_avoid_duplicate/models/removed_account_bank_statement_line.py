from odoo import fields, models


class RemovedAccountBankStatementLine(models.Model):
    _name = "removed.account.bank.statement.line"

    date = fields.Date("Date")
    payment_ref = fields.Char("Label")
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        readonly=True,
        related="company_id.currency_id",
        store=True,
    )
    amount = fields.Monetary("Amount", readonly=True)
    statement_id = fields.Many2one(
        comodel_name="account.bank.statement", string="Bank Statement"
    )
