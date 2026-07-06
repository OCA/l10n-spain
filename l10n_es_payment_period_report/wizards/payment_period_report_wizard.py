# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class L10nEsPaymentPeriodReportWizard(models.TransientModel):
    _name = "l10n.es.payment.period.report.wizard"
    _description = "Spanish supplier payment period report wizard"

    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    year = fields.Integer(
        string="Fiscal year", required=True, default=lambda self: self._default_year()
    )
    date_from = fields.Date(
        required=True, default=lambda self: self._default_date_from()
    )
    date_to = fields.Date(required=True, default=lambda self: self._default_date_to())
    method = fields.Selection(
        selection=[
            ("normal", "Normal annual accounts"),
            ("abbreviated", "Abbreviated annual accounts or SME"),
        ],
        required=True,
        default="normal",
        help="Normal: weighted paid and pending operations ratios (ICAC "
        "Resolution 29/01/2016, art. 5.1-5.4) plus the paid invoices figures of "
        "Law 18/2022.\n"
        "Abbreviated or SME: average trade creditors balance over net purchases "
        "and external services, multiplied by 365 (art. 5.5).",
    )
    legal_payment_days = fields.Integer(required=True, default=60)
    date_start_type = fields.Selection(
        selection=[
            ("invoice_date", "Invoice date"),
            ("date", "Accounting date"),
        ],
        string="Start date",
        required=True,
        default="invoice_date",
    )
    line_ids = fields.One2many(
        comodel_name="l10n.es.payment.period.report.line",
        inverse_name="wizard_id",
        string="Supplier operations",
        readonly=True,
    )
    total_amount_paid = fields.Monetary(
        currency_field="currency_id", readonly=True, string="Total payments made"
    )
    total_amount_pending = fields.Monetary(
        currency_field="currency_id", readonly=True, string="Total payments pending"
    )
    paid_operations_ratio = fields.Float(
        readonly=True, string="Ratio of paid operations"
    )
    pending_operations_ratio = fields.Float(
        readonly=True, string="Ratio of operations pending payment"
    )
    total_amount_paid_within = fields.Monetary(
        currency_field="currency_id",
        readonly=True,
        string="Amount paid within legal period",
    )
    invoice_count = fields.Integer(readonly=True, string="Number of invoices")
    invoice_count_within = fields.Integer(
        readonly=True, string="Invoices paid within legal period"
    )
    amount_within_percent = fields.Float(readonly=True, string="Amount %")
    invoice_within_percent = fields.Float(readonly=True, string="Invoices %")
    average_payment_period = fields.Float(
        readonly=True, string="Average payment period to suppliers"
    )
    creditor_opening_balance = fields.Monetary(
        currency_field="currency_id",
        readonly=True,
        string="Trade creditors opening balance",
    )
    creditor_closing_balance = fields.Monetary(
        currency_field="currency_id",
        readonly=True,
        string="Trade creditors closing balance",
    )
    creditor_average_balance = fields.Monetary(
        currency_field="currency_id",
        readonly=True,
        string="Average trade creditors balance",
    )
    net_purchases = fields.Monetary(
        currency_field="currency_id", readonly=True, string="Net purchases"
    )
    external_services = fields.Monetary(
        currency_field="currency_id", readonly=True, string="External services"
    )
    computed_method = fields.Selection(
        selection=lambda self: self._fields["method"].selection,
        readonly=True,
        help="Method of the figures shown, which may differ from the selected "
        "one until the report is computed again.",
    )

    @api.model
    def _default_year(self):
        return fields.Date.context_today(self).year

    @api.model
    def _default_date_from(self):
        today = fields.Date.context_today(self)
        return today.replace(month=1, day=1)

    @api.model
    def _default_date_to(self):
        today = fields.Date.context_today(self)
        return today.replace(month=12, day=31)

    @api.onchange("year")
    def _onchange_year(self):
        if self.year:
            self.date_from = fields.Date.to_date(f"{self.year}-01-01")
            self.date_to = fields.Date.to_date(f"{self.year}-12-31")

    def _check_parameters(self):
        self.ensure_one()
        if self.date_from > self.date_to:
            raise UserError(_("Start date must be before end date."))
        if self.legal_payment_days <= 0:
            raise UserError(_("Legal payment days must be greater than zero."))

    def _get_report_data(self):
        self.ensure_one()
        self._check_parameters()
        return self.env["account.move"].l10n_es_payment_period_report_data(
            self.company_id,
            self.date_from,
            self.date_to,
            self.legal_payment_days,
            self.date_start_type,
            self.method,
        )

    def _prepare_line_values(self, line):
        return dict(line, wizard_id=self.id)

    def _get_summary_fields(self):
        """Result fields of both methods, reset before each computation."""
        return [
            "total_amount_paid",
            "total_amount_pending",
            "paid_operations_ratio",
            "pending_operations_ratio",
            "average_payment_period",
            "total_amount_paid_within",
            "amount_within_percent",
            "invoice_count",
            "invoice_count_within",
            "invoice_within_percent",
            "creditor_opening_balance",
            "creditor_closing_balance",
            "creditor_average_balance",
            "net_purchases",
            "external_services",
        ]

    def action_compute(self):
        self.ensure_one()
        data = self._get_report_data()
        self.line_ids.unlink()
        self.env["l10n.es.payment.period.report.line"].create(
            [self._prepare_line_values(line) for line in data["lines"]]
        )
        values = dict.fromkeys(self._get_summary_fields(), False)
        values.update(data["summary"], computed_method=self.method)
        self.write(values)
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
        }

    def action_export_xlsx(self):
        self.ensure_one()
        if self.computed_method != self.method:
            self.action_compute()
        return self.env.ref(
            "l10n_es_payment_period_report.payment_period_report_xlsx"
        ).report_action(self)

    def action_view_lines(self):
        self.ensure_one()
        if self.computed_method != self.method:
            self.action_compute()
        return {
            "type": "ir.actions.act_window",
            "name": _("Supplier Payment Period Detail"),
            "res_model": "l10n.es.payment.period.report.line",
            "view_mode": "tree,form",
            "domain": [("wizard_id", "=", self.id)],
            "context": {"search_default_group_by_line_type": 1},
            "target": "current",
        }

    def get_report_file_name(self):
        self.ensure_one()
        return f"payment_period_report_{self.year}"


class L10nEsPaymentPeriodReportLine(models.TransientModel):
    _name = "l10n.es.payment.period.report.line"
    _description = "Spanish supplier payment period report line"
    _order = "line_type, payment_date, move_id, id"

    wizard_id = fields.Many2one(
        comodel_name="l10n.es.payment.period.report.wizard",
        required=True,
        ondelete="cascade",
    )
    currency_id = fields.Many2one(related="wizard_id.currency_id")
    line_type = fields.Selection(
        selection=[("paid", "Paid"), ("pending", "Pending payment")],
        string="Type",
        readonly=True,
    )
    move_id = fields.Many2one(
        comodel_name="account.move", string="Invoice", readonly=True
    )
    payment_move_id = fields.Many2one(
        comodel_name="account.move", string="Payment entry", readonly=True
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner", string="Supplier", readonly=True
    )
    invoice_date = fields.Date(readonly=True)
    accounting_date = fields.Date(readonly=True)
    date_start = fields.Date(readonly=True, string="Start date")
    payment_date = fields.Date(readonly=True)
    amount = fields.Monetary(
        currency_field="currency_id",
        readonly=True,
        help="Amount paid, or amount pending payment at the end of the period.",
    )
    days = fields.Integer(
        readonly=True,
        help="Days from the start date to the payment, or to the end of the "
        "period for pending operations.",
    )
    within_legal_period = fields.Boolean(readonly=True)

    def name_get(self):
        return [
            (line.id, f"{line.move_id.name or ''} - {line.partner_id.name or ''}")
            for line in self
        ]
