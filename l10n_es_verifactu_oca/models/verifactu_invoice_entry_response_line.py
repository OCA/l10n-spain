# Copyright 2025 ForgeFlow S.L.
# Copyright 2026 César Andrés Sánchez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.base.models.ir_model import MODULE_UNINSTALL_FLAG

from ..models.verifactu_invoice_entry import VERIFACTU_SEND_STATES


class VerifactuInvoiceEntryResponseLine(models.Model):
    _name = "verifactu.invoice.entry.response.line"
    _description = "VERI*FACTU send log"
    _order = "id desc"

    entry_id = fields.Many2one(comodel_name="verifactu.invoice.entry", required=True)
    entry_response_id = fields.Many2one("verifactu.invoice.entry.response")
    model = fields.Char(readonly=True)
    document_id = fields.Many2oneReference(
        string="Document", model_field="model", readonly=True, index=True
    )
    response = fields.Text()
    send_state = fields.Selection(
        selection=VERIFACTU_SEND_STATES,
        string="VERI*FACTU send state",
        default="not_sent",
        readonly=True,
        copy=False,
        help="Indicates the state of this document in relation with the "
        "presentation to VERI*FACTU.",
    )
    verifactu_csv = fields.Text(related="entry_response_id.verifactu_csv")
    error_code = fields.Char()
    document_name = fields.Char(related="entry_id.document_name", readonly=True)
    is_cancellation = fields.Boolean(
        string="Is cancellation",
        compute="_compute_is_cancellation",
        readonly=True,
        help="Indicates whether this response line is related to a "
        "cancellation request.",
    )

    @property
    def document(self):
        return self.env[self.model].browse(self.document_id).exists()

    @api.depends("entry_id.entry_type")
    def _compute_is_cancellation(self):
        for rec in self:
            rec.is_cancellation = rec.entry_id.entry_type == "cancel"

    def unlink(self):
        """Keep send evidence for sealed entries (same policy as the entry)."""
        self.check_access("unlink")
        if not self.env.context.get(
            "verifactu_force_unlink"
        ) and not self.env.context.get(MODULE_UNINSTALL_FLAG):
            sealed_lines = self.filtered(
                lambda r: r.entry_id and r.entry_id._is_verifactu_sealed()
            )
            if sealed_lines:
                raise UserError(
                    _(
                        "You cannot delete VERI*FACTU response lines linked to "
                        "sealed invoice entries."
                    )
                )
        return super().unlink()
