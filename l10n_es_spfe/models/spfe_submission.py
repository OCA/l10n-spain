# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import config, split_every

_logger = logging.getLogger(__name__)

SPFE_OPERATION_TYPES = [
    ("send", "Submit Invoices (SUBMITINVOICE)"),
    ("cancel", "Cancel Invoice (CANCELINVOICE)"),
    ("query_id", "Query by ID (QUERYBYID)"),
    ("query_filter", "Query by Date Filter (QUERYBYFILTER)"),
    ("download_id", "Download by ID (DOWNLOADBYID)"),
    ("download_loc", "Download by Locator (DOWNLOADBYLOC)"),
    ("customer_events", "Customer Events - Payment/Rejection"),
    ("supplier_events", "Supplier Events - Settlement/Default"),
    ("validate_pre", "Pre-Validation (PRE only)"),
]


class L10nEsSpfeSubmission(models.Model):
    _name = "l10n.es.spfe.submission"
    _description = "AEAT SPFE Submission Log"
    _inherit = ["mail.thread"]
    _order = "id desc"

    name = fields.Char(
        string="Reference",
        required=True,
        readonly=True,
        default="/",
        copy=False,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        readonly=True,
        default=lambda self: self.env.company,
    )
    operation_type = fields.Selection(
        selection=SPFE_OPERATION_TYPES,
        string="Operation",
        required=True,
        readonly=True,
    )
    state = fields.Selection(
        selection=[
            ("accepted", "Accepted (200)"),
            ("partial", "Partially Accepted (406)"),
            ("rejected", "Rejected (400)"),
            ("error", "Error"),
        ],
        string="Result",
        required=True,
        readonly=True,
        tracking=True,
    )
    send_date = fields.Datetime(
        string="Execution Date",
        required=True,
        readonly=True,
        default=fields.Datetime.now,
    )
    message_id = fields.Char(string="ebMS Message ID", readonly=True)
    response_id = fields.Char(string="AEAT Response ID", readonly=True)
    response_code = fields.Char(readonly=True)
    response_description = fields.Text(string="Response Summary", readonly=True)
    request_soap_xml = fields.Text(string="SOAP Request Envelope", readonly=True)
    response_xml = fields.Text(string="DocumentStatus / Response XML", readonly=True)
    line_ids = fields.One2many(
        comodel_name="l10n.es.spfe.submission.line",
        inverse_name="submission_id",
        string="Invoice Lines",
        readonly=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("l10n.es.spfe.submission")
                    or "/"
                )
        return super().create(vals_list)

    @api.model
    def _map_response_code_to_state(self, code):
        if code == "200":
            return "accepted"
        if code == "406":
            return "partial"
        if code == "400":
            return "rejected"
        return "error"

    @api.model
    def _commit_if_allowed(self):
        if not config["test_enable"] and not self.env.context.get("spfe_no_commit"):
            self.env.cr.commit()  # pylint: disable=invalid-commit

    @api.model
    def _cron_send_company_invoices(self, company):
        domain = [
            ("company_id", "=", company.id),
            ("state", "=", "posted"),
            ("move_type", "in", ("out_invoice", "out_refund")),
            ("journal_id.spfe_enabled", "=", True),
            ("spfe_state", "=", "not_sent"),
        ]
        if company.spfe_start_date:
            domain.append(("invoice_date", ">=", company.spfe_start_date))
        pending_moves = (
            self.env["account.move"]
            .search(domain, order="invoice_date asc, id asc")
            .filtered("spfe_enabled")
        )
        ready_moves = self.env["account.move"]
        for move in pending_moves:
            try:
                move._check_spfe_invoice_ready()
                ready_moves |= move
            except UserError as err:
                move.write({"spfe_state": "rejected", "spfe_last_error": str(err)})
                self._commit_if_allowed()
        for batch in split_every(100, ready_moves.ids):
            batch_moves = self.env["account.move"].browse(batch)
            err_msg = False
            try:
                with self.env.cr.savepoint():
                    batch_moves.action_spfe_send_invoice()
            except Exception as err:  # noqa: BLE001
                err_msg = str(err)
                _logger.warning(
                    "SPFE cron send skipped/deferred for %s: %s",
                    batch_moves.mapped("name"),
                    err_msg,
                )
            if err_msg:
                batch_moves.write({"spfe_last_error": err_msg})
            self._commit_if_allowed()

    @api.model
    def _cron_send_pending_spfe_invoices(self):
        """Send pending SPFE invoices and full payment/collection events."""
        companies = self.env["res.company"].search([("spfe_enabled", "=", True)])
        for company in companies:
            if company.spfe_auto_send:
                self._cron_send_company_invoices(company)
            if company.spfe_auto_send_payment:
                pay_moves = self.env["account.move"].search(
                    [
                        ("company_id", "=", company.id),
                        ("spfe_payment_pending", "=", True),
                    ],
                    order="invoice_date asc, id asc",
                )
                if pay_moves:
                    pay_moves._auto_send_spfe_payment_status_safe()
                    self._commit_if_allowed()
        return True


class L10nEsSpfeSubmissionLine(models.Model):
    _name = "l10n.es.spfe.submission.line"
    _description = "AEAT SPFE Submission Document Line"
    _order = "id desc"

    submission_id = fields.Many2one(
        comodel_name="l10n.es.spfe.submission",
        required=True,
        ondelete="cascade",
    )
    company_id = fields.Many2one(
        related="submission_id.company_id",
        store=True,
        readonly=True,
    )
    operation_type = fields.Selection(
        related="submission_id.operation_type",
        store=True,
        readonly=True,
    )
    send_date = fields.Datetime(
        related="submission_id.send_date",
        store=True,
        readonly=True,
    )
    move_id = fields.Many2one(
        comodel_name="account.move",
        string="Invoice",
        ondelete="set null",
        index=True,
    )
    invoice_number = fields.Char()
    invoice_date = fields.Date(string="Issue Date")
    issuer_vat = fields.Char(string="Issuer NIF")
    status_code = fields.Char()
    status_description = fields.Text(string="Description / Error")
    spfe_locator = fields.Char(string="SPFE Locator")
    payload_xml = fields.Text(string="UBL Payload XML")
