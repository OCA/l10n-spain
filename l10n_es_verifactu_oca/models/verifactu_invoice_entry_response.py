# Copyright 2025 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, fields, models


class VerifactuInvoiceEntryResponse(models.Model):
    _name = "verifactu.invoice.entry.response"
    _description = "VERI*FACTU Send Response"
    _inherit = ["mail.activity.mixin", "mail.thread"]
    _order = "id desc"

    header = fields.Text()
    name = fields.Char()
    invoice_data = fields.Text()
    response = fields.Text()
    verifactu_csv = fields.Text(string="VERI*FACTU CSV")
    date_response = fields.Datetime(readonly=True)
    activity_type_id = fields.Many2one(
        "mail.activity.type",
        string="Activity Type",
        compute="_compute_activity_type_id",
        store=True,
    )
    response_line_ids = fields.One2many(
        "verifactu.invoice.entry.response.line",
        "entry_response_id",
        string="Response lines",
    )

    def _compute_activity_type_id(self):
        for record in self:
            activity = self.env["mail.activity"].search(
                [
                    ("res_model", "=", "verifactu.invoice.entry.response"),
                    ("res_id", "=", record.id),
                ],
                limit=1,
            )
            record.activity_type_id = activity.activity_type_id if activity else False

    def create_activity_on_exception(self):
        model_id = self.env["ir.model"]._get_id("verifactu.invoice.entry.response")
        exception_activity_type = self.env.ref(
            "l10n_es_verifactu_oca.mail_activity_data_exception"
        )
        activity_vals = []
        responsible_group = self.env.ref(
            "l10n_es_verifactu_oca.group_verifactu_responsible"
        )
        users = responsible_group.users
        for record in self:
            existing = self.env["mail.activity"].search_count(
                [
                    ("activity_type_id", "=", exception_activity_type.id),
                    ("res_model", "=", "verifactu.invoice.entry.response"),
                ],
                limit=1,
            )
            if not existing:
                user = users[:1] or self.env.user
                activity_vals.append(
                    {
                        "res_model_id": model_id,
                        "res_model": "verifactu.invoice.entry.response",
                        "res_id": record.id,
                        "activity_type_id": exception_activity_type.id,
                        "user_id": user.id,
                        "summary": _("Check connection error with VERI*FACTU"),
                        "note": _(
                            "There has been an error when trying to connect to "
                            "VERI*FACTU"
                        ),
                    }
                )
        if activity_vals:
            return self.env["mail.activity"].create(activity_vals)
        return False

    def create_send_response_activity(self):
        activity_type = self.env.ref("mail.mail_activity_data_warning")
        model_id = self.env["ir.model"]._get_id("verifactu.invoice.entry.response")
        activity_vals = []
        responsible_group = self.env.ref(
            "l10n_es_verifactu_oca.group_verifactu_responsible"
        )
        users = responsible_group.users
        for record in self:
            user = users[:1] or self.env.user
            activity_vals.append(
                {
                    "activity_type_id": activity_type.id,
                    "user_id": user.id,
                    "res_id": record.id,
                    "res_model": "verifactu.invoice.entry.response",
                    "res_model_id": model_id,
                    "summary": _("Check incorrect invoices from VERI*FACTU"),
                    "note": _("There is an error with one or more invoices"),
                }
            )
        return self.env["mail.activity"].create(activity_vals)

    def complete_open_activity_on_exception(self):
        exception_activity_type = self.env.ref(
            "l10n_es_verifactu_oca.mail_activity_data_exception"
        )
        for _record in self:
            activity = self.env["mail.activity"].search(
                [
                    ("activity_type_id", "=", exception_activity_type.id),
                    ("res_model", "=", "verifactu.invoice.entry.response"),
                ],
            )
        for act in activity:
            if act.state != "done":
                act.action_done()
        return True
