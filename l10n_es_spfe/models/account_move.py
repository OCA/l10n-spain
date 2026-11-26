# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import datetime
import logging
import re

from lxml import etree

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import config, split_every

_logger = logging.getLogger(__name__)

SPFE_INVOICE_TYPES = [
    ("380", "[380] Factura ordinaria (art. 6, 7.2 y 7.3 RD 1619/2012)"),
    ("384", "[384] Factura rectificativa"),
    ("388", "[388] Factura en sustitución de facturas simplificadas"),
    ("389", "[389] Factura emitida por el destinatario"),
    ("471", "[471] Factura rectificativa emitida por el destinatario"),
]

SPFE_REFUND_TYPES = [
    ("R1", "[R1] Error fundado en derecho y Art. 80.Uno, Dos y Seis LIVA"),
    ("R2", "[R2] Concurso de acreedores (Art. 80.Tres LIVA)"),
    ("R3", "[R3] Créditos incobrables (Art. 80.Cuatro LIVA)"),
    ("R4", "[R4] Resto de causas"),
]


class AccountMove(models.Model):
    _inherit = "account.move"

    spfe_enabled = fields.Boolean(
        string="SPFE Enabled",
        compute="_compute_spfe_enabled",
    )
    spfe_company_test = fields.Boolean(
        related="company_id.spfe_test",
        readonly=True,
    )
    spfe_state = fields.Selection(
        selection=[
            ("not_sent", "Not Sent"),
            ("validated_pre", "Pre-Validated (PRE)"),
            ("sent", "Registered in SPFE"),
            ("rejected", "Rejected by SPFE"),
            ("cancelled", "Cancelled in SPFE"),
        ],
        string="SPFE Status",
        default="not_sent",
        copy=False,
        readonly=True,
        tracking=True,
    )
    spfe_customer_status = fields.Selection(
        selection=[
            ("none", "Pending / Accepted"),
            ("paid", "Paid (PAYMENT)"),
            ("rejected", "Rejected (REJECTION)"),
        ],
        string="SPFE Customer Event Status",
        default="none",
        copy=False,
        readonly=True,
        tracking=True,
    )
    spfe_supplier_status = fields.Selection(
        selection=[
            ("none", "Pending / Accepted"),
            ("settled", "Settled / Collected (SETTLEMENT)"),
            ("defaulted", "Unpaid / Default (DEFAULT)"),
        ],
        string="SPFE Supplier Event Status",
        default="none",
        copy=False,
        readonly=True,
        tracking=True,
    )
    spfe_locator = fields.Char(
        string="SPFE Locator",
        copy=False,
        readonly=True,
        index=True,
        help="Unique external locator assigned by AEAT SPFE (LOCGENV1:...).",
    )
    spfe_last_error = fields.Text(
        string="SPFE Last Message / Error",
        copy=False,
        readonly=True,
    )
    spfe_ubl_attachment_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="SPFE UBL 2.5 XML",
        copy=False,
        readonly=True,
    )
    spfe_submission_line_ids = fields.One2many(
        comodel_name="l10n.es.spfe.submission.line",
        inverse_name="move_id",
        string="SPFE Logs",
        copy=False,
        readonly=True,
    )
    spfe_invoice_type = fields.Selection(
        selection=SPFE_INVOICE_TYPES,
        string="SPFE Invoice Type",
        compute="_compute_spfe_invoice_type",
        store=True,
        readonly=False,
        help="BT-3: Invoice type code according to SPFE Lista L1.",
    )
    spfe_copy_indicator = fields.Boolean(
        string="SPFE Faithful Copy",
        default=False,
        copy=False,
        help="BT-ES-1: Mark when issuing a faithful copy of the original invoice.",
    )
    spfe_refund_type = fields.Selection(
        selection=SPFE_REFUND_TYPES,
        string="SPFE Rectificativa Type",
        compute="_compute_spfe_refund_fields",
        store=True,
        readonly=False,
        help="Lista L2.A: Legal ground for corrective invoice.",
    )
    spfe_refund_mode = fields.Selection(
        selection=[
            ("I", "[I] By differences (Por diferencias)"),
            ("S", "[S] By substitution (Por sustitución)"),
        ],
        string="SPFE Rectificativa Mode",
        compute="_compute_spfe_refund_fields",
        store=True,
        readonly=False,
        help="Lista L2.B: Corrective invoice mode (differences or substitution).",
    )
    spfe_rectified_move_ids = fields.Many2many(
        comodel_name="account.move",
        relation="account_move_spfe_rectified_rel",
        column1="move_id",
        column2="rectified_move_id",
        string="SPFE Referenced Preceding Invoices",
        copy=False,
        help="BG-3: Preceding invoices rectified by this corrective invoice.",
    )
    spfe_rectified_base = fields.Monetary(
        string="Rectified Base",
        currency_field="currency_id",
        copy=False,
        help="Lista L2.C: Rectified taxable base in substitution mode.",
    )
    spfe_rectified_tax = fields.Monetary(
        string="Rectified VAT Quota",
        currency_field="currency_id",
        copy=False,
        help="Lista L2.C: Rectified VAT quota in substitution mode.",
    )
    spfe_rectified_surcharge = fields.Monetary(
        string="Rectified RE Surcharge",
        currency_field="currency_id",
        copy=False,
        help="Lista L2.C: Rectified equivalence surcharge in substitution mode.",
    )
    spfe_operation_date = fields.Date(
        string="SPFE Operation Date",
        copy=False,
        help="BT-7: Effective operation/tax point date when different from issue date.",
    )
    spfe_prepaid_date = fields.Date(
        string="SPFE Prepaid Effective Date",
        copy=False,
        help="BT-ES-2: Effective payment date when collected in advance.",
    )
    spfe_period_start_date = fields.Date(
        string="SPFE Summary Period Start",
        copy=False,
        help="BT-73: Summary invoice period start date.",
    )
    spfe_period_end_date = fields.Date(
        string="SPFE Summary Period End",
        copy=False,
        help="BT-74: Summary invoice period end date.",
    )
    spfe_note_code = fields.Char(
        string="SPFE Note Code",
        help="BT-21: UNTDID 4451 subject code (e.g. 'REG' for regulatory mentions).",
    )
    spfe_note = fields.Text(
        string="SPFE Invoice Note",
        help="BT-22: Invoice note included in UBL Annotation.",
    )
    spfe_third_party_issuer_id = fields.Many2one(
        comodel_name="res.partner",
        string="SPFE Third-Party Issuer",
        copy=False,
        help="BG-ES-1: Third party materially issuing this invoice.",
    )
    spfe_qr_type = fields.Selection(
        selection=[
            ("VERIFACTU", "VERI*FACTU"),
            ("TICKETBAI", "TicketBAI"),
        ],
        string="SPFE Fiscal QR Type",
        default="VERIFACTU",
    )
    spfe_qr_url = fields.Char(
        string="SPFE Fiscal QR URL",
        copy=False,
        help="BT-ES-25: Verification URL encoded in the fiscal QR.",
    )
    spfe_payment_pending = fields.Boolean(
        string="SPFE Payment / Collection Pending",
        compute="_compute_spfe_payment_pending",
        store=True,
        help="Indicates that a full collection (SETTLEMENT), full payment "
        "(PAYMENT), or its cancellation is pending communication to AEAT SPFE.",
    )

    def button_draft(self):
        if self.filtered(lambda m: m.spfe_state == "sent"):
            raise UserError(
                self.env._(
                    "An invoice registered in SPFE cannot be reset to "
                    "draft. Issue a corrective invoice instead."
                )
            )
        return super().button_draft()

    def _get_spfe_due_date(self):
        """Return payment due date applying Ley 3/2004 (30 days) when unspecified."""
        self.ensure_one()
        if self.invoice_payment_term_id and self.invoice_date_due:
            return self.invoice_date_due
        if (
            self.invoice_date_due
            and self.invoice_date
            and self.invoice_date_due > self.invoice_date
        ):
            return self.invoice_date_due
        if self.invoice_date:
            return self.invoice_date + datetime.timedelta(days=30)
        return self.invoice_date_due

    def _get_pending_spfe_payment_action(self):
        self.ensure_one()
        if not self.spfe_enabled or self.state != "posted" or self.spfe_state != "sent":
            return False
        if self.move_type in ("out_invoice", "out_refund"):
            if self.payment_state == "paid" and self.spfe_supplier_status != "settled":
                return "SETTLEMENT"
            if (
                self.payment_state not in ("paid", "in_payment")
                and self.spfe_supplier_status == "settled"
            ):
                return "CANCELSETTLEMENT"
        elif self.move_type in ("in_invoice", "in_refund"):
            if not self.ref:
                return False
            if self.payment_state == "paid" and self.spfe_customer_status != "paid":
                return "PAYMENT"
            if (
                self.payment_state not in ("paid", "in_payment")
                and self.spfe_customer_status == "paid"
            ):
                return "CANCELPAYMENT"
        return False

    @api.depends(
        "company_id.spfe_enabled",
        "company_id.spfe_start_date",
        "journal_id.spfe_enabled",
        "partner_id.commercial_partner_id.spfe_exclude",
        "partner_id.commercial_partner_id.vat",
        "partner_id.commercial_partner_id.country_id",
        "invoice_date",
        "ref",
        "state",
        "spfe_state",
        "payment_state",
        "spfe_supplier_status",
        "spfe_customer_status",
        "move_type",
    )
    def _compute_spfe_payment_pending(self):
        for move in self:
            move.spfe_payment_pending = bool(move._get_pending_spfe_payment_action())

    def _trigger_spfe_cron_async(self):
        if config["test_enable"]:
            return
        cron = self.env.ref(
            "l10n_es_spfe.ir_cron_spfe_send_pending", raise_if_not_found=False
        )
        if cron:
            cron.sudo()._trigger()

    def _compute_payment_state(self):
        prev = {m.id: m.payment_state for m in self if m._origin.id}
        res = super()._compute_payment_state()
        changed = self.filtered(
            lambda m: m.id in prev
            and prev[m.id] != m.payment_state
            and m.company_id.spfe_enabled
            and m.company_id.spfe_auto_send_payment
            and m.spfe_state == "sent"
        )
        if changed:
            changed._compute_spfe_payment_pending()
            self._trigger_spfe_cron_async()
        return res

    @api.depends(
        "company_id.spfe_enabled",
        "company_id.spfe_start_date",
        "journal_id.spfe_enabled",
        "partner_id.commercial_partner_id.spfe_exclude",
        "partner_id.commercial_partner_id.vat",
        "partner_id.commercial_partner_id.country_id",
        "move_type",
        "invoice_date",
    )
    def _compute_spfe_enabled(self):
        for move in self:
            enabled = bool(
                move.company_id.spfe_enabled
                and move.journal_id.spfe_enabled
                and move.move_type
                in ("out_invoice", "out_refund", "in_invoice", "in_refund")
                and not move.partner_id.commercial_partner_id.spfe_exclude
                and move.partner_id._has_spfe_spanish_nif()
            )
            if (
                enabled
                and move.invoice_date
                and move.company_id.spfe_start_date
                and move.invoice_date < move.company_id.spfe_start_date
            ):
                enabled = False
            move.spfe_enabled = enabled

    @api.depends("move_type")
    def _compute_spfe_invoice_type(self):
        for move in self:
            if move.move_type in ("out_refund", "in_refund"):
                move.spfe_invoice_type = "384"
            elif move.move_type in ("out_invoice", "in_invoice"):
                move.spfe_invoice_type = move.spfe_invoice_type or "380"
            else:
                move.spfe_invoice_type = False

    @api.depends("move_type", "spfe_invoice_type")
    def _compute_spfe_refund_fields(self):
        for move in self:
            if move.spfe_invoice_type in ("384", "471"):
                move.spfe_refund_type = move.spfe_refund_type or "R1"
                move.spfe_refund_mode = move.spfe_refund_mode or "I"
            else:
                move.spfe_refund_type = False
                move.spfe_refund_mode = False

    def _post(self, soft=True):
        posted = super()._post(soft=soft)
        auto_moves = posted.filtered(
            lambda m: m.spfe_enabled
            and m.company_id.spfe_auto_send
            and m.move_type in ("out_invoice", "out_refund")
            and m.spfe_state == "not_sent"
        )
        if auto_moves:
            self._trigger_spfe_cron_async()
        return posted

    def _get_spfe_rectified_moves(self):
        self.ensure_one()
        moves = self.spfe_rectified_move_ids
        if not moves and self.reversed_entry_id:
            moves = self.reversed_entry_id
        return moves

    def _get_spfe_qr_info(self):
        self.ensure_one()
        if self.spfe_qr_url:
            return self.spfe_qr_url, self.spfe_qr_type or "VERIFACTU"
        if hasattr(self, "verifactu_qr_url") and self.verifactu_qr_url:
            return self.verifactu_qr_url, "VERIFACTU"
        for tbai_attr in ("tbai_qr_url", "ticketbai_qr_url"):
            if hasattr(self, tbai_attr) and getattr(self, tbai_attr):
                return getattr(self, tbai_attr), "TICKETBAI"
        return False, False

    def _extract_spfe_raw_iban(self):
        self.ensure_one()
        if self.partner_bank_id:
            return (
                self.partner_bank_id.sanitized_acc_number
                or self.partner_bank_id.acc_number
            )
        pmode = self.payment_mode_id
        if not pmode:
            return False
        journal = pmode.fixed_journal_id or pmode.variable_journal_ids[:1]
        if journal and journal.bank_account_id:
            bank = journal.bank_account_id
            return bank.sanitized_acc_number or bank.acc_number
        return False

    def _get_spfe_payment_means_info(self):
        """Return (unece_4461_code, clean_iban) enforcing SPFE-CORE-18."""
        self.ensure_one()
        code = (
            self.payment_mode_id.payment_method_id.unece_code
            if (self.payment_mode_id and self.payment_mode_id.payment_method_id)
            else False
        )
        iban_raw = self._extract_spfe_raw_iban()
        iban = re.sub(r"\s+", "", iban_raw).upper() if iban_raw else False
        if not code:
            code = "30" if iban else "10"
        if code in ("30", "49") and not iban:
            code = "1"
        if code not in ("30", "49"):
            iban = False
        return code, iban

    def _check_spfe_party_addresses(self):
        self.ensure_one()
        parties = (
            (self.env._("Seller"), self.company_id.partner_id.commercial_partner_id),
            (self.env._("Customer"), self.partner_id.commercial_partner_id),
        )
        for label, partner in parties:
            partner._get_spfe_party_tax_info()
            if not (partner.street or partner.street2) or not partner.country_id:
                raise UserError(
                    self.env._(
                        "%(role)s '%(name)s' must have street and country "
                        "configured for SPFE (BR-ES-8 / BR-ES-10).",
                        role=label,
                        name=partner.display_name,
                    )
                )
            missing_es = partner.country_id.code == "ES" and not (
                partner.city and partner.zip and partner.state_id
            )
            if missing_es:
                raise UserError(
                    self.env._(
                        "Spanish %(role)s '%(name)s' must have city, ZIP code, "
                        "and province configured for SPFE (BR-ES-9 / BR-ES-11).",
                        role=label,
                        name=partner.display_name,
                    )
                )

    def _check_spfe_summary_period(self):
        start = self.spfe_period_start_date
        end = self.spfe_period_end_date
        if not (start and end):
            return
        if start >= end or (start.year, start.month) != (end.year, end.month):
            raise UserError(
                self.env._(
                    "Summary invoice period (BG-14) start and end dates must "
                    "belong to the same month and year with StartDate < EndDate "
                    "(BR-ES-3 / BR-ES-4)."
                )
            )

    def _check_spfe_invoice_ready(self):
        self.ensure_one()
        if self.state != "posted":
            raise UserError(
                self.env._(
                    "Invoice '%(inv)s' must be posted before generating SPFE XML.",
                    inv=self.display_name,
                )
            )
        if not self.invoice_date:
            raise UserError(
                self.env._(
                    "Invoice '%(inv)s' is missing an issue date.",
                    inv=self.display_name,
                )
            )
        min_date = self.company_id.spfe_start_date
        if min_date and self.invoice_date < min_date:
            raise UserError(
                self.env._(
                    "Invoice '%(inv)s' date (%(date)s) is earlier than SPFE "
                    "entry into force (%(start)s).",
                    inv=self.display_name,
                    date=self.invoice_date,
                    start=min_date,
                )
            )
        self._check_spfe_party_addresses()
        self._check_spfe_summary_period()
        product_lines = self.invoice_line_ids.filtered(
            lambda ln: ln.display_type == "product" and not ln.spfe_collection_line_type
        )
        if not product_lines:
            raise UserError(
                self.env._(
                    "Invoice '%(inv)s' has no invoice lines for SPFE.",
                    inv=self.display_name,
                )
            )

    def _generate_and_attach_spfe_ubl(self):
        self.ensure_one()
        xml_bytes = self.env["base.ubl"].spfe_generate_invoice_ubl_xml(self)
        safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", self.name or f"inv_{self.id}")
        filename = f"SPFE_{safe_name}.xml"
        vals = {
            "name": filename,
            "type": "binary",
            "datas": base64.b64encode(xml_bytes),
            "mimetype": "application/xml",
            "res_model": "account.move",
            "res_id": self.id,
        }
        if self.spfe_ubl_attachment_id:
            self.spfe_ubl_attachment_id.write(vals)
        else:
            att = self.env["ir.attachment"].create(vals)
            self.spfe_ubl_attachment_id = att.id
        return xml_bytes

    def action_spfe_generate_ubl_xml(self):
        for move in self:
            if move.move_type not in ("out_invoice", "out_refund"):
                raise UserError(
                    self.env._("Only customer invoices can be submitted to SPFE.")
                )
            move._generate_and_attach_spfe_ubl()
        if len(self) == 1 and self.spfe_ubl_attachment_id:
            return {
                "type": "ir.actions.act_url",
                "url": (f"/web/content/{self.spfe_ubl_attachment_id.id}?download=true"),
                "target": "self",
            }
        return False

    def action_spfe_validate_pre(self):
        """Validate customer invoices against AEAT PRE ValidationInvoiceSOAP."""
        for move in self:
            if move.move_type not in ("out_invoice", "out_refund"):
                raise UserError(
                    self.env._("Only customer invoices can be submitted to SPFE.")
                )
            if move.spfe_state == "sent":
                raise UserError(
                    self.env._(
                        "Invoice '%(inv)s' is already registered in SPFE.",
                        inv=move.display_name,
                    )
                )
            move._validate_single_spfe_pre()
        return True

    def _validate_single_spfe_pre(self):
        self.ensure_one()
        xml_bytes = self._generate_and_attach_spfe_ubl()
        res = self.env["l10n.es.spfe.soap"].validate_invoice_pre(
            self.company_id, xml_bytes
        )
        st = res["status_dict"]
        sub = self.env["l10n.es.spfe.submission"].create(
            {
                "company_id": self.company_id.id,
                "operation_type": "validate_pre",
                "state": self.env[
                    "l10n.es.spfe.submission"
                ]._map_response_code_to_state(st["response_code"]),
                "response_id": st["id"],
                "response_code": st["response_code"],
                "response_description": st["description"],
                "request_soap_xml": res["request_soap_xml"].decode("utf-8"),
                "response_xml": res["response_xml"].decode("utf-8"),
            }
        )
        _s, _t, issuer_vat = self.company_id.partner_id._get_spfe_party_tax_info()
        errors = []
        for item in st["items"] or [
            {
                "status_code": st["response_code"],
                "description": st["description"],
                "locator": False,
            }
        ]:
            self.env["l10n.es.spfe.submission.line"].create(
                {
                    "submission_id": sub.id,
                    "move_id": self.id,
                    "invoice_number": self.name,
                    "invoice_date": self.invoice_date,
                    "issuer_vat": issuer_vat,
                    "status_code": item.get("status_code"),
                    "status_description": item.get("description"),
                    "payload_xml": xml_bytes.decode("utf-8"),
                }
            )
            if item.get("status_code") != "200" and item.get("description"):
                errors.append(f"[{item.get('status_code')}] {item.get('description')}")
        if st["response_code"] == "200":
            if self.spfe_state == "not_sent":
                self.spfe_state = "validated_pre"
            self.spfe_last_error = False
        else:
            self.spfe_last_error = "\n".join(errors) or st["description"]
        return True

    def action_spfe_send_invoice(self):
        """Submit customer invoices in batches of up to 100 to SendInvoiceSOAP."""
        valid_moves = self.filtered(
            lambda m: m.move_type in ("out_invoice", "out_refund")
        )
        if not valid_moves:
            raise UserError(
                self.env._("Only customer invoices can be submitted to SPFE.")
            )
        for company in valid_moves.mapped("company_id"):
            comp_moves = valid_moves.filtered(lambda m, c=company: m.company_id == c)
            for batch_ids in split_every(100, comp_moves.ids):
                self.browse(batch_ids)._send_spfe_batch(company)
        paid_sent = valid_moves.filtered(
            lambda m: m.spfe_state == "sent"
            and m.company_id.spfe_auto_send_payment
            and m.payment_state == "paid"
        )
        if paid_sent:
            paid_sent._compute_spfe_payment_pending()
            self._trigger_spfe_cron_async()
        return True

    def _get_spfe_reconciliation_effective_date(self):
        self.ensure_one()
        today = fields.Date.context_today(self)
        rec_lines = self.line_ids.filtered(
            lambda ln: ln.account_id.account_type
            in ("asset_receivable", "liability_payable")
        )
        partials = rec_lines.matched_debit_ids | rec_lines.matched_credit_ids
        dates = []
        for part in partials:
            cpart = (
                part.credit_move_id
                if part.debit_move_id.move_id == self
                else part.debit_move_id
            )
            if cpart.date:
                dates.append(cpart.date)
        eff_date = max(dates) if dates else today
        return min(eff_date, today)

    def _has_spfe_posted_refunds(self):
        self.ensure_one()
        if self.reversal_move_ids.filtered(lambda r: r.state == "posted"):
            return True
        return bool(
            self.search_count(
                [
                    ("spfe_rectified_move_ids", "in", self.id),
                    ("state", "=", "posted"),
                ],
                limit=1,
            )
        )

    @api.model
    def _normalize_spfe_vat_key(self, raw_vat):
        vat = re.sub(r"[\s.-]", "", (raw_vat or "").upper())
        if vat.startswith("ES") and len(vat) > 2:
            vat = vat[2:]
        return vat

    def _build_auto_spfe_event_dict(self, action_code):
        self.ensure_one()
        is_customer = self.move_type in ("in_invoice", "in_refund")
        issuer = (
            self.partner_id.commercial_partner_id
            if is_customer
            else self.company_id.partner_id.commercial_partner_id
        )
        _s, _t, issuer_vat = issuer._get_spfe_party_tax_info()
        inv_num = self.ref if is_customer else self.name
        if not inv_num:
            raise UserError(
                self.env._(
                    "Vendor bill '%(inv)s' is missing the supplier invoice "
                    "reference required by SPFE.",
                    inv=self.display_name,
                )
            )
        return {
            "response_code": action_code,
            "effective_date": self._get_spfe_reconciliation_effective_date(),
            "due_date": self._get_spfe_due_date(),
            "is_corrected_invoice": self._has_spfe_posted_refunds(),
            "is_negative_invoice": self.move_type in ("in_refund", "out_refund"),
            "id": inv_num,
            "issue_date": self.invoice_date,
            "issuer_vat": issuer_vat,
            "issuer_name": issuer.name,
        }

    def _apply_spfe_event_response_items(
        self, st, move_by_key, move_by_num, action_code
    ):
        status_field = (
            "spfe_customer_status"
            if action_code in ("PAYMENT", "CANCELPAYMENT")
            else "spfe_supplier_status"
        )
        new_status = {
            "PAYMENT": "paid",
            "CANCELPAYMENT": "none",
            "SETTLEMENT": "settled",
            "CANCELSETTLEMENT": "none",
        }[action_code]
        errors = []
        items = st["items"] or [
            {
                "id": num,
                "issuer_vat": vat,
                "status_code": st["response_code"],
                "description": st["description"],
            }
            for (num, vat) in move_by_key
        ]
        for item in items:
            item_vat = self._normalize_spfe_vat_key(item.get("issuer_vat"))
            move = move_by_key.get((item.get("id"), item_vat))
            if not move and not item_vat and len(move_by_key) == 1:
                move = move_by_num.get(item.get("id"))
            if not move:
                continue
            if (item.get("status_code") or st["response_code"]) == "200":
                move.write({status_field: new_status, "spfe_last_error": False})
            else:
                msg = item.get("description") or st["description"]
                move.spfe_last_error = msg
                errors.append(f"{move.display_name}: {msg}")
        return errors

    def _send_spfe_payment_events_batch(self, company, action_code):
        events = []
        move_by_key = {}
        move_by_num = {}
        for move in self:
            ev = move._build_auto_spfe_event_dict(action_code)
            events.append(ev)
            move_by_key[(ev["id"], ev["issuer_vat"])] = move
            move_by_num[ev["id"]] = move
        app_xml = self.env["base.ubl"].spfe_generate_invoice_events_xml(
            action_code, events
        )
        service_key = (
            "customer_events"
            if action_code in ("PAYMENT", "CANCELPAYMENT")
            else "supplier_events"
        )
        resp = self.env["l10n.es.spfe.soap"].call_ebms_service(
            company,
            service_key,
            attachments=[(f"{action_code}.xml", app_xml)],
        )
        ds_bytes = next(iter(resp["attachments"].values()), None)
        if not ds_bytes:
            raise UserError(
                self.env._("AEAT SPFE response did not include DocumentStatus.")
            )
        st = self.env["base.ubl"].spfe_parse_document_status_xml(ds_bytes)
        sub = self.env["l10n.es.spfe.submission"].create(
            {
                "company_id": company.id,
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
        payload_txt = app_xml.decode("utf-8")
        for ev in events:
            mv = move_by_key[(ev["id"], ev["issuer_vat"])]
            self.env["l10n.es.spfe.submission.line"].create(
                {
                    "submission_id": sub.id,
                    "move_id": mv.id,
                    "invoice_number": ev["id"],
                    "invoice_date": ev["issue_date"],
                    "issuer_vat": ev["issuer_vat"],
                    "status_code": st["response_code"],
                    "status_description": st["description"],
                    "payload_xml": payload_txt,
                }
            )
        errors = self._apply_spfe_event_response_items(
            st, move_by_key, move_by_num, action_code
        )
        if errors:
            raise UserError(
                self.env._(
                    "SPFE rejected status event: %(msg)s",
                    msg="; ".join(errors),
                )
            )
        return sub

    def _auto_send_spfe_payment_status_safe(self):
        """Communicate full collection/payment to SPFE safely inside a savepoint."""
        pending = self.filtered(
            lambda m: m.spfe_payment_pending
            and not self.env.context.get("skip_spfe_auto_payment")
        )
        grouped = {}
        for move in pending:
            act = move._get_pending_spfe_payment_action()
            if act:
                grouped.setdefault((move.company_id, act), self.browse())
                grouped[(move.company_id, act)] |= move
        for (company, act), moves in grouped.items():
            for batch_ids in split_every(100, moves.ids):
                batch = self.browse(batch_ids)
                err_msg = False
                try:
                    with self.env.cr.savepoint():
                        batch.with_context(
                            skip_spfe_auto_payment=True
                        )._send_spfe_payment_events_batch(company, act)
                except Exception as err:  # noqa: BLE001
                    err_msg = str(err)
                    _logger.warning(
                        "SPFE auto %s skipped/deferred for %s: %s",
                        act,
                        batch.mapped("name"),
                        err_msg,
                    )
                if err_msg:
                    batch.write({"spfe_last_error": err_msg})

    def action_spfe_send_payment_status(self):
        """Manually send pending full collection (SETTLEMENT) or payment (PAYMENT)."""
        self._compute_spfe_payment_pending()
        pending = self.filtered("spfe_payment_pending")
        if not pending:
            raise UserError(
                self.env._(
                    "No selected invoice has a pending full collection or "
                    "payment status change to communicate to SPFE."
                )
            )
        grouped = {}
        for move in pending:
            act = move._get_pending_spfe_payment_action()
            if act:
                grouped.setdefault((move.company_id, act), self.browse())
                grouped[(move.company_id, act)] |= move
        for (company, act), moves in grouped.items():
            for batch_ids in split_every(100, moves.ids):
                self.browse(batch_ids).with_context(
                    skip_spfe_auto_payment=True
                )._send_spfe_payment_events_batch(company, act)
        return True

    def _send_spfe_batch(self, company):
        attachments = []
        move_by_number = {}
        payload_by_move = {}
        for idx, move in enumerate(self, start=1):
            if move.spfe_state == "sent":
                raise UserError(
                    self.env._(
                        "Invoice '%(inv)s' is already registered in SPFE.",
                        inv=move.display_name,
                    )
                )
            xml_bytes = move._generate_and_attach_spfe_ubl()
            cid = f"invoice_{idx}_{move.id}.xml"
            attachments.append((cid, xml_bytes))
            move_by_number[move.name] = move
            payload_by_move[move.id] = xml_bytes.decode("utf-8")

        resp = self.env["l10n.es.spfe.soap"].call_ebms_service(
            company, "send", attachments=attachments
        )
        ds_bytes = next(iter(resp["attachments"].values()), None)
        if not ds_bytes:
            raise UserError(
                self.env._("AEAT SPFE response did not include DocumentStatus.")
            )
        st = self.env["base.ubl"].spfe_parse_document_status_xml(ds_bytes)
        sub = self.env["l10n.es.spfe.submission"].create(
            {
                "company_id": company.id,
                "operation_type": "send",
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
        _s, _t, comp_vat = company.partner_id._get_spfe_party_tax_info()
        grouped_errors = {}
        for item in st["items"]:
            move = move_by_number.get(item["id"])
            self.env["l10n.es.spfe.submission.line"].create(
                {
                    "submission_id": sub.id,
                    "move_id": move.id if move else False,
                    "invoice_number": item["id"],
                    "invoice_date": move.invoice_date if move else False,
                    "issuer_vat": item.get("issuer_vat") or comp_vat,
                    "status_code": item.get("status_code"),
                    "status_description": item.get("description"),
                    "spfe_locator": item.get("locator"),
                    "payload_xml": payload_by_move.get(move.id, "") if move else "",
                }
            )
            if move:
                if item.get("status_code") == "200":
                    move.write(
                        {
                            "spfe_state": "sent",
                            "spfe_locator": item.get("locator") or move.spfe_locator,
                            "spfe_last_error": False,
                        }
                    )
                else:
                    grouped_errors.setdefault(move.id, []).append(
                        f"[{item.get('status_code')}] {item.get('description')}"
                    )
        for move_id, errs in grouped_errors.items():
            self.browse(move_id).write(
                {
                    "spfe_state": "rejected",
                    "spfe_last_error": "\n".join(errs),
                }
            )
        return sub

    def action_spfe_query_status(self):
        """Query SPFE status and locator by invoice ID (GetInvoicesSOAP)."""
        for move in self:
            if move.state != "posted":
                raise UserError(
                    self.env._(
                        "Invoice '%(inv)s' must be posted before generating SPFE XML.",
                        inv=move.display_name,
                    )
                )
        for company in self.mapped("company_id"):
            moves = self.filtered(lambda m, c=company: m.company_id == c)
            for is_supplier, role in (
                (True, "AccountingSupplierParty"),
                (False, "AccountingCustomerParty"),
            ):
                role_moves = moves.filtered(
                    lambda m, sup=is_supplier: (
                        m.move_type in ("out_invoice", "out_refund")
                    )
                    == sup
                )
                if role_moves:
                    role_moves._query_spfe_by_id(company, role)
        return True

    def _build_spfe_doc_refs_for_role(self, company, role):
        doc_refs = []
        move_by_key = {}
        move_by_num = {}
        for move in self:
            issuer_partner = (
                company.partner_id
                if role == "AccountingSupplierParty"
                else move.partner_id
            ).commercial_partner_id
            _s, _t, issuer_vat = issuer_partner._get_spfe_party_tax_info()
            inv_num = move.name if role == "AccountingSupplierParty" else move.ref
            if not inv_num:
                raise UserError(
                    self.env._(
                        "Vendor bill '%(inv)s' is missing the supplier invoice "
                        "reference required by SPFE.",
                        inv=move.display_name,
                    )
                )
            doc_refs.append(
                {
                    "id": inv_num,
                    "issue_date": move.invoice_date,
                    "issuer_vat": issuer_vat,
                    "issuer_name": issuer_partner.name,
                }
            )
            norm_vat = self._normalize_spfe_vat_key(issuer_vat)
            move_by_key[(inv_num, norm_vat)] = move
            move_by_num[inv_num] = move
        return doc_refs, move_by_key, move_by_num

    def _query_spfe_by_id(self, company, role):
        doc_refs, move_by_key, move_by_num = self._build_spfe_doc_refs_for_role(
            company, role
        )
        query_xml = self.env["base.ubl"].spfe_generate_query_or_download_by_id_xml(
            "QUERYBYID", doc_refs
        )
        resp = self.env["l10n.es.spfe.soap"].call_ebms_service(
            company,
            "query_id",
            attachments=[("ConsultaFacturasPorIDs.xml", query_xml)],
            message_properties=[("Role", role)],
        )
        ds_bytes = next(iter(resp["attachments"].values()), None)
        if not ds_bytes:
            return False
        st = self.env["base.ubl"].spfe_parse_document_status_xml(ds_bytes)
        sub = self.env["l10n.es.spfe.submission"].create(
            {
                "company_id": company.id,
                "operation_type": "query_id",
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
        for item in st["items"]:
            item_vat = self._normalize_spfe_vat_key(item.get("issuer_vat"))
            move = move_by_key.get((item["id"], item_vat))
            if not move and not item_vat and len(move_by_key) == 1:
                move = move_by_num.get(item["id"])
            self.env["l10n.es.spfe.submission.line"].create(
                {
                    "submission_id": sub.id,
                    "move_id": move.id if move else False,
                    "invoice_number": item["id"],
                    "status_code": item.get("status_code"),
                    "status_description": item.get("description"),
                    "spfe_locator": item.get("locator"),
                    "issuer_vat": item.get("issuer_vat"),
                }
            )
            if move and item.get("locator"):
                vals = {"spfe_locator": item["locator"]}
                if move.spfe_state == "not_sent":
                    vals["spfe_state"] = "sent"
                move.write(vals)
        return sub

    def action_spfe_download_by_id(self):
        """Download SPFE UBL 2.5 XML by invoice ID (DownloadInvoicesByIDSOAP)."""
        for move in self:
            if move.state != "posted":
                raise UserError(
                    self.env._(
                        "Invoice '%(inv)s' must be posted before generating SPFE XML.",
                        inv=move.display_name,
                    )
                )
        for company in self.mapped("company_id"):
            moves = self.filtered(lambda m, c=company: m.company_id == c)
            for is_supplier, role in (
                (True, "AccountingSupplierParty"),
                (False, "AccountingCustomerParty"),
            ):
                role_moves = moves.filtered(
                    lambda m, sup=is_supplier: (
                        m.move_type in ("out_invoice", "out_refund")
                    )
                    == sup
                )
                for batch_ids in split_every(100, role_moves.ids):
                    self.browse(batch_ids)._download_spfe_by_id(company, role)
        return True

    def _attach_downloaded_spfe_ubl(self, inv_xml):
        self.ensure_one()
        raw_name = (
            (self.ref or self.name)
            if self.move_type in ("in_invoice", "in_refund")
            else self.name
        ) or f"inv_{self.id}"
        safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", raw_name)
        vals = {
            "name": f"SPFE_DL_{safe_name}.xml",
            "type": "binary",
            "datas": base64.b64encode(inv_xml),
            "mimetype": "application/xml",
            "res_model": "account.move",
            "res_id": self.id,
        }
        if self.spfe_ubl_attachment_id:
            self.spfe_ubl_attachment_id.write(vals)
        else:
            att = self.env["ir.attachment"].create(vals)
            self.spfe_ubl_attachment_id = att.id

    def _download_spfe_by_id(self, company, role):
        doc_refs, move_by_key, move_by_num = self._build_spfe_doc_refs_for_role(
            company, role
        )
        dl_xml = self.env["base.ubl"].spfe_generate_query_or_download_by_id_xml(
            "DOWNLOADBYID", doc_refs
        )
        resp = self.env["l10n.es.spfe.soap"].call_ebms_service(
            company,
            "download_id",
            attachments=[("DescargarFacturasPorIDs.xml", dl_xml)],
            message_properties=[("Role", role)],
        )
        sub_vals = {
            "company_id": company.id,
            "operation_type": "download_id",
            "state": "accepted",
            "message_id": resp["message_id"],
            "response_code": "200",
            "request_soap_xml": resp["request_soap_xml"].decode("utf-8"),
        }
        inv_attachments = []
        for att_bytes in resp["attachments"].values():
            root = etree.fromstring(att_bytes)
            local_name = etree.QName(root).localname
            if local_name == "DocumentStatus":
                st = self.env["base.ubl"].spfe_parse_document_status_xml(att_bytes)
                sub_vals.update(
                    {
                        "state": self.env[
                            "l10n.es.spfe.submission"
                        ]._map_response_code_to_state(st["response_code"]),
                        "response_id": st["id"],
                        "response_code": st["response_code"],
                        "response_description": st["description"],
                        "response_xml": att_bytes.decode("utf-8"),
                    }
                )
            elif local_name == "Invoice":
                inv_attachments.append((root, att_bytes))
        if not sub_vals.get("response_description"):
            sub_vals["response_description"] = self.env._(
                "Downloaded %(count)s UBL invoices.",
                count=len(inv_attachments),
            )
        sub = self.env["l10n.es.spfe.submission"].create(sub_vals)
        _nsmap, ns_braced = self.env["base.ubl"]._ubl_get_nsmap_namespace("Invoice-2")
        ns = {k: v.strip("{}") for k, v in ns_braced.items()}
        ubl_helper = self.env["base.ubl"]
        for inv_root, inv_xml in inv_attachments:
            inv_id = ubl_helper._spfe_xpath_text(inv_root, "cbc:ID", ns)
            supp_vat = self._normalize_spfe_vat_key(
                ubl_helper._spfe_xpath_text(
                    inv_root,
                    "cac:AccountingSupplierParty/cac:Party/"
                    "cac:PartyTaxScheme/cbc:CompanyID",
                    ns,
                )
            )
            move = move_by_key.get((inv_id, supp_vat))
            if not move and not supp_vat and len(move_by_key) == 1:
                move = move_by_num.get(inv_id)
            if move:
                move._attach_downloaded_spfe_ubl(inv_xml)
                if move.spfe_state == "not_sent":
                    move.spfe_state = "sent"
            self.env["l10n.es.spfe.submission.line"].create(
                {
                    "submission_id": sub.id,
                    "move_id": move.id if move else False,
                    "invoice_number": inv_id,
                    "invoice_date": move.invoice_date if move else False,
                    "issuer_vat": supp_vat,
                    "status_code": "200",
                    "payload_xml": inv_xml.decode("utf-8"),
                }
            )
        return sub

    def action_open_spfe_cancel_wizard(self):
        self.ensure_one()
        if self.spfe_state != "sent":
            raise UserError(
                self.env._("Only invoices registered in SPFE can be cancelled in SPFE.")
            )
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Cancel Invoice in SPFE"),
            "res_model": "l10n.es.spfe.cancel.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_move_id": self.id},
        }

    def action_open_spfe_event_wizard(self):
        self.ensure_one()
        if self.state != "posted":
            raise UserError(
                self.env._(
                    "Invoice '%(inv)s' must be posted before generating SPFE XML.",
                    inv=self.display_name,
                )
            )
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Communicate SPFE Invoice Status"),
            "res_model": "l10n.es.spfe.event.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_move_id": self.id},
        }
