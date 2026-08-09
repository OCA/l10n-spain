# Copyright 2026 Odoo Community Association (OCA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError

EXTERNAL_INVOICE_TYPES = ("out_invoice", "out_refund")


class AccountMove(models.Model):
    _inherit = "account.move"

    external_sif_id = fields.Char(
        string="External SIF ID",
        help="Identifier of the SIF that issued the original invoice.",
        copy=False,
    )
    external_sif_installation = fields.Char(
        string="External SIF installation",
        help="Installation number of the SIF that issued the original invoice.",
        copy=False,
    )
    external_rf_identifier = fields.Char(
        string="External billing record ID",
        help="Identifier of the original billing record, when available.",
        copy=False,
    )
    is_external_invoice = fields.Boolean(
        string="Invoice issued by an external SIF",
        compute="_compute_is_external_invoice",
        store=True,
        index=True,
    )

    @api.depends("journal_id.verifactu_import_journal", "move_type")
    def _compute_is_external_invoice(self):
        for move in self:
            move.is_external_invoice = bool(
                move.journal_id.verifactu_import_journal
                and move.move_type in EXTERNAL_INVOICE_TYPES
            )

    def _check_external_invoice_output(self):
        if self.filtered("is_external_invoice"):
            raise UserError(
                _(
                    "Invoices issued by an external SIF cannot be previewed, printed, "
                    "or sent from Odoo."
                )
            )

    def action_invoice_print(self):
        self._check_external_invoice_output()
        return super().action_invoice_print()

    def action_invoice_sent(self):
        self._check_external_invoice_output()
        return super().action_invoice_sent()

    def action_send_and_print(self):
        self._check_external_invoice_output()
        return super().action_send_and_print()

    def preview_invoice(self):
        self._check_external_invoice_output()
        return super().preview_invoice()
