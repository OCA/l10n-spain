# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError

CUSTOMER_ACTIONS = ("PAYMENT", "CANCELPAYMENT", "REJECTION", "CANCELREJECTION")
SUPPLIER_ACTIONS = ("SETTLEMENT", "CANCELSETTLEMENT", "DEFAULT", "CANCELDEFAULT")


class L10nEsSpfeEventWizard(models.TransientModel):
    _name = "l10n.es.spfe.event.wizard"
    _description = "Communicate Invoice Payment / Rejection / Settlement Status to SPFE"

    move_id = fields.Many2one(
        comodel_name="account.move",
        string="Invoice",
        required=True,
        readonly=True,
    )
    party_role = fields.Selection(
        selection=[
            ("customer", "Customer / Recipient (Pago / Rechazo)"),
            ("supplier", "Supplier / Issuer (Cobro / Impago)"),
        ],
        string="Role",
        compute="_compute_party_role",
        store=True,
    )
    response_code = fields.Selection(
        selection=[
            ("PAYMENT", "PAYMENT - Pago efectivo completo (Destinatario)"),
            ("CANCELPAYMENT", "CANCELPAYMENT - Anulación de pago (Destinatario)"),
            ("REJECTION", "REJECTION - Rechazo de factura (Destinatario)"),
            (
                "CANCELREJECTION",
                "CANCELREJECTION - Anulación de rechazo (Destinatario)",
            ),
            ("SETTLEMENT", "SETTLEMENT - Cobro efectivo completo (Emisor)"),
            ("CANCELSETTLEMENT", "CANCELSETTLEMENT - Anulación de cobro (Emisor)"),
            ("DEFAULT", "DEFAULT - Impago (Emisor)"),
            ("CANCELDEFAULT", "CANCELDEFAULT - Anulación de impago (Emisor)"),
        ],
        string="Event Type",
        required=True,
    )
    effective_date = fields.Date(default=fields.Date.context_today)
    due_date = fields.Date(string="Payment Due Date")
    shipment_date = fields.Date(string="Goods / Services Receipt Date")
    reception_date = fields.Date(string="Invoice Reception Date")
    rejection_reason = fields.Selection(
        selection=[
            ("01", "[01] Rechazo comercial"),
            ("02", "[02] Consumo particular o no afecto a la actividad"),
        ],
        string="Rejection Reason (Anexo II L1)",
        default="01",
    )
    is_corrected_invoice = fields.Boolean(string="Previously Rectified Invoice")
    is_negative_invoice = fields.Boolean(string="Negative Rectificativa Invoice")
    financing_arrangement = fields.Boolean(string="Collected via Financing Arrangement")

    @api.depends("move_id")
    def _compute_party_role(self):
        for wiz in self:
            if wiz.move_id.move_type in ("in_invoice", "in_refund"):
                wiz.party_role = "customer"
            else:
                wiz.party_role = "supplier"

    @api.onchange("move_id")
    def _onchange_move_id_defaults(self):
        if not self.move_id:
            return
        self.due_date = self.move_id._get_spfe_due_date()
        self.is_corrected_invoice = self.move_id._has_spfe_posted_refunds()
        self.is_negative_invoice = self.move_id.move_type in ("in_refund", "out_refund")
        if self.move_id.move_type in ("in_invoice", "in_refund"):
            self.response_code = "PAYMENT"
        else:
            self.response_code = "SETTLEMENT"

    def _validate_event_inputs(self):
        self.ensure_one()
        move = self.move_id
        if self.party_role == "customer" and self.response_code not in CUSTOMER_ACTIONS:
            raise UserError(
                self.env._(
                    "Action %(code)s is only valid for issuer/supplier invoices.",
                    code=self.response_code,
                )
            )
        if self.party_role == "supplier" and self.response_code not in SUPPLIER_ACTIONS:
            raise UserError(
                self.env._(
                    "Action %(code)s is only valid for recipient/customer bills.",
                    code=self.response_code,
                )
            )
        today = fields.Date.context_today(self)
        if self.response_code in ("PAYMENT", "REJECTION", "SETTLEMENT", "DEFAULT"):
            if not self.effective_date:
                raise UserError(
                    self.env._(
                        "Effective Date is mandatory for %(code)s.",
                        code=self.response_code,
                    )
                )
            if self.effective_date > today:
                raise UserError(
                    self.env._(
                        "Effective Date cannot be later than today "
                        "(BR-PAGO-2 / BR-COBRO-2)."
                    )
                )
        if self.response_code == "PAYMENT" and not self.due_date:
            raise UserError(
                self.env._("Payment Due Date is mandatory for PAYMENT (BR-PAGO-3).")
            )
        if (
            self.response_code == "REJECTION"
            and move.invoice_date
            and self.effective_date <= move.invoice_date
        ):
            raise UserError(
                self.env._(
                    "Rejection date must be after the invoice issue date "
                    "(BR-RECHAZO-3)."
                )
            )
        if (
            self.reception_date
            and move.invoice_date
            and self.reception_date < move.invoice_date
        ):
            raise UserError(
                self.env._(
                    "Invoice reception date must be equal to or after issue date."
                )
            )

    def action_send_event(self):
        self.ensure_one()
        self._validate_event_inputs()
        move = self.move_id
        issuer = (
            move.partner_id.commercial_partner_id
            if self.party_role == "customer"
            else move.company_id.partner_id.commercial_partner_id
        )
        _s, _t, issuer_vat = issuer._get_spfe_party_tax_info()
        inv_num = (
            (move.ref or move.name) if self.party_role == "customer" else move.name
        )
        ev_dict = {
            "response_code": self.response_code,
            "effective_date": self.effective_date,
            "due_date": self.due_date,
            "shipment_date": self.shipment_date,
            "reception_date": self.reception_date,
            "rejection_reason": self.rejection_reason,
            "is_corrected_invoice": self.is_corrected_invoice,
            "is_negative_invoice": self.is_negative_invoice,
            "financing_arrangement": self.financing_arrangement,
            "id": inv_num,
            "issue_date": move.invoice_date,
            "issuer_vat": issuer_vat,
            "issuer_name": issuer.name,
        }
        app_xml = self.env["base.ubl"].spfe_generate_invoice_events_xml(
            self.response_code, [ev_dict]
        )
        service_key = (
            "customer_events" if self.party_role == "customer" else "supplier_events"
        )
        resp = self.env["l10n.es.spfe.soap"].call_ebms_service(
            move.company_id,
            service_key,
            attachments=[(f"{self.response_code}.xml", app_xml)],
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
                "operation_type": service_key,
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
        item = st["items"][0] if st["items"] else {}
        self.env["l10n.es.spfe.submission.line"].create(
            {
                "submission_id": sub.id,
                "move_id": move.id,
                "invoice_number": inv_num,
                "invoice_date": move.invoice_date,
                "issuer_vat": issuer_vat,
                "status_code": item.get("status_code") or st["response_code"],
                "status_description": item.get("description") or st["description"],
                "payload_xml": app_xml.decode("utf-8"),
            }
        )
        if st["response_code"] != "200":
            err = item.get("description") or st["description"]
            move.spfe_last_error = err
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": self.env._("SPFE Event Rejected"),
                    "message": self.env._(
                        "SPFE rejected status event: %(msg)s", msg=err
                    ),
                    "type": "danger",
                    "sticky": True,
                    "next": {"type": "ir.actions.act_window_close"},
                },
            }
        self._update_move_event_status(move)
        return {"type": "ir.actions.act_window_close"}

    def _update_move_event_status(self, move):
        customer_map = {
            "PAYMENT": "paid",
            "CANCELPAYMENT": "none",
            "REJECTION": "rejected",
            "CANCELREJECTION": "none",
        }
        supplier_map = {
            "SETTLEMENT": "settled",
            "CANCELSETTLEMENT": "none",
            "DEFAULT": "defaulted",
            "CANCELDEFAULT": "none",
        }
        vals = {"spfe_last_error": False}
        if self.response_code in customer_map:
            vals["spfe_customer_status"] = customer_map[self.response_code]
        if self.response_code in supplier_map:
            vals["spfe_supplier_status"] = supplier_map[self.response_code]
        move.write(vals)
