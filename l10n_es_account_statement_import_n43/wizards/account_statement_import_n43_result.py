# Copyright 2026 Domatix
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountStatementImportN43Result(models.TransientModel):
    _name = "account.statement.import.n43.result"
    _description = "N43 import review of possible duplicates"

    import_wizard_id = fields.Many2one(
        "account.statement.import", required=True, ondelete="cascade"
    )
    mode = fields.Selection(
        [("statements", "Show statements"), ("reconcile", "Reconcile")],
        required=True,
        default="statements",
    )
    line_ids = fields.One2many("account.statement.import.n43.result.line", "wizard_id")

    def action_import(self):
        """Import the file skipping the movements left marked as duplicates."""
        self.ensure_one()
        wizard = self.import_wizard_id.with_context(
            n43_duplicate_decisions={
                line.unique_import_id: line.is_duplicate for line in self.line_ids
            }
        )
        if self.mode == "reconcile":
            return wizard.import_file_and_reconcile_button()
        return wizard.import_file_button()


class AccountStatementImportN43ResultLine(models.TransientModel):
    _name = "account.statement.import.n43.result.line"
    _description = "N43 import possible duplicate"
    _order = "date, id"

    wizard_id = fields.Many2one(
        "account.statement.import.n43.result", required=True, ondelete="cascade"
    )
    unique_import_id = fields.Char(readonly=True)
    reason = fields.Selection(
        [
            ("imported", "Already imported"),
            ("repeated", "Repeated in the file"),
        ],
        readonly=True,
    )
    is_duplicate = fields.Boolean(
        string="Duplicate",
        help="Marked movements are not imported.",
    )
    date = fields.Date(readonly=True)
    amount = fields.Float(digits=(16, 2), readonly=True)
    payment_ref = fields.Char(readonly=True)
    matched_line_id = fields.Many2one("account.bank.statement.line", readonly=True)
    matched_statement_name = fields.Char(
        related="matched_line_id.statement_id.name", readonly=True
    )
