# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.exceptions import UserError


class L10nEsSpfeCancelWizard(models.TransientModel):
    _name = "l10n.es.spfe.cancel.wizard"
    _description = "Cancel Invoice in AEAT SPFE"

    move_id = fields.Many2one(
        comodel_name="account.move",
        string="Invoice",
        required=True,
        readonly=True,
    )
    effective_date = fields.Date(
        string="Cancellation Date",
        required=True,
        default=fields.Date.context_today,
    )
    reason = fields.Char(
        string="Cancellation Reason",
        required=True,
        default="Anulación por emisión errónea / inexistencia de operación",
    )

    def action_confirm_cancel(self):
        self.ensure_one()
        move = self.move_id
        if move.spfe_state != "sent":
            raise UserError(
                self.env._("Only invoices registered in SPFE can be cancelled in SPFE.")
            )
        app_xml = self.env["base.ubl"].spfe_generate_cancel_response_xml(
            move,
            effective_date=self.effective_date,
            reason=self.reason,
        )
        resp = self.env["l10n.es.spfe.soap"].call_ebms_service(
            move.company_id,
            "cancel",
            attachments=[("CancelarFact.xml", app_xml)],
        )
        ds_bytes = next(iter(resp["attachments"].values()), None)
        if not ds_bytes:
            raise UserError(
                self.env._("AEAT SPFE response did not include DocumentStatus.")
            )
        st = self.env["base.ubl"].spfe_parse_document_status_xml(ds_bytes)
        sub = self.env["l10n.es.spfe.submission"].create(
            {
                "company_id": move.company_id.id,
                "operation_type": "cancel",
                "state": self.env[
                    "l10n.es.spfe.submission"
                ]._map_response_code_to_state(st["response_code"]),
                "message_id": resp["message_id"],
                "response_id": st["id"],
                "response_code": st["response_code"],
                "response_description": st["description"],
                "request_soap_xml": resp["request_soap_xml"].decode("utf-8"),
                "response_xml": ds_bytes.decode("utf-8"),
            }
        )
        _s, _t, comp_vat = move.company_id.partner_id._get_spfe_party_tax_info()
        item = st["items"][0] if st["items"] else {}
        self.env["l10n.es.spfe.submission.line"].create(
            {
                "submission_id": sub.id,
                "move_id": move.id,
                "invoice_number": move.name,
                "invoice_date": move.invoice_date,
                "issuer_vat": comp_vat,
                "status_code": item.get("status_code") or st["response_code"],
                "status_description": item.get("description") or st["description"],
                "payload_xml": app_xml.decode("utf-8"),
            }
        )
        if st["response_code"] == "200":
            move.write({"spfe_state": "cancelled", "spfe_last_error": False})
            move.message_post(
                body=self.env._(
                    "Invoice cancelled in AEAT SPFE (reason: %(reason)s). "
                    "Note: the accounting entry remains posted in Odoo.",
                    reason=self.reason,
                )
            )
            return {"type": "ir.actions.act_window_close"}
        err = item.get("description") or st["description"]
        move.spfe_last_error = err
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": self.env._("SPFE Cancellation Rejected"),
                "message": self.env._(
                    "SPFE rejected invoice cancellation: %(msg)s", msg=err
                ),
                "type": "danger",
                "sticky": True,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }
