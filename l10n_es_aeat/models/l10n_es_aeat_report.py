# Copyright 2004-2011 Pexego Sistemas Informáticos - Luis Manuel Angueira
# Copyright 2013 - Acysos S.L. - Ignacio Ibeas (Migración a v7)
# Copyright 2016 Tecnativa - Antonio Espinosa
# Copyright 2014-2021 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
from calendar import monthrange
from datetime import datetime

from odoo import _, api, exceptions, fields, models
from odoo.tools import config

from .spanish_states_mapping import SPANISH_STATES as ss


class L10nEsAeatReport(models.AbstractModel):
    _name = "l10n.es.aeat.report"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "AEAT report base module"
    _order = "date_start,id"
    _rec_name = "name"
    _aeat_number = False
    _period_quarterly = True
    _period_monthly = True
    _period_yearly = False
    SPANISH_STATES = ss

    def _default_journal(self):
        return self.env["account.journal"].search(
            [("type", "=", "general"), ("company_id", "=", self.env.company.id)]
        )[:1]

    def get_period_type_selection(self):
        period_types = []
        if self._period_yearly or config["test_enable"]:
            period_types += [("0A", "0A - Anual")]
        if self._period_quarterly:
            period_types += [
                ("1T", "1T - Primer trimestre"),
                ("2T", "2T - Segundo trimestre"),
                ("3T", "3T - Tercer trimestre"),
                ("4T", "4T - Cuarto trimestre"),
            ]
        if self._period_monthly or config["test_enable"]:
            period_types += [
                ("01", "01 - Enero"),
                ("02", "02 - Febrero"),
                ("03", "03 - Marzo"),
                ("04", "04 - Abril"),
                ("05", "05 - Mayo"),
                ("06", "06 - Junio"),
                ("07", "07 - Julio"),
                ("08", "08 - Agosto"),
                ("09", "09 - Septiembre"),
                ("10", "10 - Octubre"),
                ("11", "11 - Noviembre"),
                ("12", "12 - Diciembre"),
            ]
        return period_types

    def _default_period_type(self):
        selection = self.get_period_type_selection()
        return selection and selection[0][0] or False

    def _default_year(self):
        return fields.Date.to_date(fields.Date.today()).year

    def _default_number(self):
        return self._aeat_number

    def _get_export_config(self, date):
        model = self.env["ir.model"].sudo().search([("model", "=", self._name)])
        return self.env["aeat.model.export.config"].search(
            [
                ("model_id", "=", model.id),
                ("date_start", "<=", date),
                "|",
                ("date_end", "=", False),
                ("date_end", ">=", date),
            ],
            limit=1,
        )

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        readonly=True,
        default=lambda self: self.env.company,
        states={"draft": [("readonly", False)]},
    )
    company_vat = fields.Char(
        string="VAT number",
        size=9,
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    number = fields.Char(
        string="Model number",
        size=3,
        required=True,
        readonly=True,
        default=_default_number,
    )
    previous_number = fields.Char(
        string="Previous declaration number",
        size=13,
        states={"done": [("readonly", True)]},
    )
    contact_name = fields.Char(
        string="Full Name",
        size=40,
        help="Must have name and surname.",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    contact_phone = fields.Char(
        string="Phone",
        size=9,
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    contact_email = fields.Char(
        size=50,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    representative_vat = fields.Char(
        string="L.R. VAT number",
        size=9,
        readonly=False,
        help="Legal Representative VAT number.",
        compute="_compute_representative_vat",
        store=True,
    )
    year = fields.Integer(
        default=_default_year,
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    statement_type = fields.Selection(
        selection=[("N", "Normal"), ("C", "Complementary"), ("S", "Substitutive")],
        default="N",
        readonly=True,
        required=True,
        states={"draft": [("readonly", False)]},
    )
    support_type = fields.Selection(
        selection=[("C", "DVD"), ("T", "Telematics")],
        default="T",
        readonly=True,
        required=True,
        states={"draft": [("readonly", False)]},
    )
    calculation_date = fields.Datetime()
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("calculated", "Processed"),
            ("done", "Done"),
            ("posted", "Posted"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        readonly=True,
        tracking=True,
    )
    name = fields.Char(string="Report identifier", size=13, copy=False)
    export_config_id = fields.Many2one(
        comodel_name="aeat.model.export.config",
        string="Export config",
        domain=lambda self: [
            (
                "model_id",
                "=",
                self.env["ir.model"].sudo().search([("model", "=", self._name)]).id,
            )
        ],
        compute="_compute_export_config_id",
        readonly=False,
        store=True,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        readonly=True,
        related="company_id.currency_id",
    )
    period_type = fields.Selection(
        selection="get_period_type_selection",
        required=True,
        default=_default_period_type,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    date_start = fields.Date(
        string="Starting date",
        required=True,
        readonly=True,
        store=True,
        compute="_compute_dates",
        states={"draft": [("readonly", False)]},
    )
    date_end = fields.Date(
        string="Ending date",
        required=True,
        readonly=True,
        store=True,
        compute="_compute_dates",
        states={"draft": [("readonly", False)]},
    )
    allow_posting = fields.Boolean(compute="_compute_allow_posting")
    counterpart_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Counterpart account",
        help="This account will be the counterpart for all the journal items "
        "that are regularized when posting the report.",
    )
    journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Journal",
        domain="[('type', '=', 'general'), ('company_id', '=', company_id)]",
        default=_default_journal,
        help="Journal in which post the move.",
        states={"done": [("readonly", True)]},
    )
    move_id = fields.Many2one(
        comodel_name="account.move",
        string="Account entry",
        readonly=True,
        domain=[("type", "=", "entry")],
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        related="company_id.partner_id",
        readonly=True,
    )
    partner_bank_id = fields.Many2one(
        comodel_name="res.partner.bank",
        string="Bank account",
        help="Company bank account used for the presentation",
        domain="[('acc_type', '=', 'iban'), ('partner_id', '=', partner_id)]",
    )
    error_count = fields.Integer(
        compute="_compute_error_count",
    )
    tax_agency_ids = fields.Many2many("aeat.tax.agency", string="Tax Agency")
    _sql_constraints = [
        (
            "name_uniq",
            "unique(name, company_id)",
            "AEAT report identifier must be unique",
        )
    ]

    def _compute_allow_posting(self):
        for report in self:
            report.allow_posting = False

    def _compute_error_count(self):
        """To be overridden by each report."""
        self.error_count = 0

    @api.constrains("statement_type", "previous_number")
    def _check_previous_number(self):
        for report in self:
            if report.statement_type in ("C", "S") and not report.previous_number:
                raise exceptions.UserError(
                    _(
                        "If this declaration is complementary or substitutive, "
                        "a previous declaration number should be provided."
                    )
                )

    def get_taxes_from_templates(self, tax_templates):
        company = self.company_id or self.env.user.company_id
        return company.get_taxes_from_templates(tax_templates)

    def get_account_from_template(self, account_template):
        company = self.company_id or self.env.user.company_id
        return company.get_account_from_template(account_template)

    @api.onchange("company_id")
    def onchange_company_id(self):
        """Load some company data (the VAT number) when company changes."""
        if self.company_id.vat:
            # Remove the ES part from spanish vat numbers
            #  (ES12345678Z => 12345678Z)
            self.company_vat = re.match("(ES){0,1}(.*)", self.company_id.vat).groups()[
                1
            ]
        self.contact_name = self.env.user.name
        self.contact_email = self.env.user.email
        self.contact_phone = self._filter_phone(
            self.env.user.partner_id.phone
            or self.env.user.partner_id.mobile
            or self.env.user.company_id.phone
        )
        if self.journal_id.company_id != self.company_id:
            self.journal_id = self.with_company(self.company_id.id)._default_journal()

    @api.depends("year", "period_type")
    def _compute_dates(self):
        for report in self:
            if not report.year or not report.period_type:
                continue
            else:
                if report.period_type == "0A":
                    # Anual
                    report.date_start = fields.Date.to_date("%s-01-01" % report.year)
                    report.date_end = fields.Date.to_date("%s-12-31" % report.year)
                elif report.period_type in ("1T", "2T", "3T", "4T"):
                    # Trimestral
                    starting_month = 1 + (int(report.period_type[0]) - 1) * 3
                    ending_month = starting_month + 2
                    report.date_start = fields.Date.to_date(
                        "{}-{}-01".format(report.year, starting_month)
                    )
                    report.date_end = fields.Date.to_date(
                        "%s-%s-%s"
                        % (
                            report.year,
                            ending_month,
                            monthrange(report.year, ending_month)[1],
                        )
                    )
                elif report.period_type in (
                    "01",
                    "02",
                    "03",
                    "04",
                    "05",
                    "06",
                    "07",
                    "08",
                    "09",
                    "10",
                    "11",
                    "12",
                ):
                    # Mensual
                    month = int(report.period_type)
                    report.date_start = fields.Date.to_date(
                        "{}-{}-01".format(report.year, month)
                    )
                    report.date_end = fields.Date.to_date(
                        "%s-%s-%s"
                        % (report.year, month, monthrange(report.year, month)[1])
                    )

    @api.depends("company_id")
    def _compute_representative_vat(self):
        for report in self:
            report.representative_vat = report.company_id.representative_vat

    @api.depends("date_start")
    def _compute_export_config_id(self):
        for report in self:
            date = report.date_start or fields.Date.today()
            report.export_config_id = report._get_export_config(date)

    @api.model
    def _report_identifier_get(self, vals):
        seq_name = "aeat%s-sequence" % self._aeat_number
        company_id = vals.get("company_id", self.env.user.company_id.id)
        seq = self.env["ir.sequence"].search(
            [("name", "=", seq_name), ("company_id", "=", company_id)], limit=1
        )
        if not seq:
            raise exceptions.UserError(
                _(
                    "AEAT model sequence not found. You can try to restart your "
                    "Odoo service for recreating the sequences."
                )
            )
        return seq.next_by_id()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = self._report_identifier_get(vals)
        return super().create(vals_list)

    def button_calculate(self):
        res = self.calculate()
        self.write({"state": "calculated", "calculation_date": fields.Datetime.now()})
        return res

    def button_recalculate(self):
        self.write({"calculation_date": fields.Datetime.now()})
        return self.calculate()

    def _get_previous_fiscalyear_reports(self, date):
        """Get the AEAT reports previous to the given date.

        :param date: Date for looking for previous reports.
        :return: Recordset of the previous AEAT reports. None if there is no
                 previous reports.
        """
        self.ensure_one()
        return self.search([("year", "=", self.year), ("date_start", "<", date)])

    def calculate(self):
        """To be overrided by inherit models"""
        return True

    def button_confirm(self):
        """Set report status to done."""
        self.write({"state": "done"})
        return True

    def _prepare_move_vals(self):
        self.ensure_one()
        return {
            "date": self.date_end,
            "journal_id": self.journal_id.id,
            "ref": self.name,
            "company_id": self.company_id.id,
        }

    def button_post(self):
        """Create any possible account move entry and set state to posted."""
        for report in self:
            report.create_regularization_move()
        self.write({"state": "posted"})
        return True

    def button_cancel(self):
        """Set report status to cancelled."""
        self.write({"state": "cancelled"})
        return True

    def button_unpost(self):
        """Remove created account move entry and set state to cancelled."""
        self.mapped("move_id").with_context(force_delete=True).unlink()
        self.write({"state": "cancelled"})
        return True

    def button_recover(self):
        """Set report status to draft and reset calculation date."""
        self.write({"state": "draft", "calculation_date": False})
        return True

    def button_export(self):
        for report in self:
            export_obj = self.env[
                "l10n.es.aeat.report.%s.export_to_boe" % report.number
            ]
            export_obj.export_boe_file(report)
        return True

    def button_open_move(self):
        self.ensure_one()
        action = self.env.ref("account.action_move_line_form").sudo().read()[0]
        action["view_mode"] = "form"
        action["res_id"] = self.move_id.id
        del action["view_id"]
        del action["views"]
        return action

    def unlink(self):
        if any(item.state not in ["draft", "cancelled"] for item in self):
            raise exceptions.UserError(
                _("Only reports in 'draft' or 'cancelled' state can be removed")
            )
        return super().unlink()

    @api.model
    def _prepare_aeat_sequence_vals(self, sequence, aeat_num, company):
        return {
            "name": sequence,
            "code": "aeat.sequence.type",
            "number_increment": 1,
            "implementation": "no_gap",
            "padding": 13 - len(str(aeat_num)),
            "number_next_actual": 1,
            "prefix": aeat_num,
            "company_id": company.id,
        }

    @api.model
    def _filter_phone(self, phone):
        return (phone or "").replace(" ", "")[-9:]

    def _register_hook(self, companies=None):
        res = None
        if not companies:
            res = super()._register_hook()
        if self._name in ("l10n.es.aeat.report", "l10n.es.aeat.report.tax.mapping"):
            return res
        aeat_num = getattr(self, "_aeat_number", False)
        if not aeat_num:
            raise exceptions.UserError(
                _("Modelo no válido: %s. Debe declarar una variable " "'_aeat_number'")
                % self._name
            )
        seq_obj = self.env["ir.sequence"]
        sequence = "aeat%s-sequence" % aeat_num
        if not companies:
            companies = self.env["res.company"].search([])
        for company in companies:
            seq = seq_obj.search(
                [("name", "=", sequence), ("company_id", "=", company.id)]
            )
            if seq:
                continue
            seq_obj.create(
                self.env[self._name]._prepare_aeat_sequence_vals(
                    sequence, aeat_num, company
                )
            )
        return res

    @api.model
    def _get_formatted_date(self, date):
        """Convert an Odoo date to BOE export date format.

        :param date: Date in Odoo format or falsy value
        :return: Date formatted for BOE export.
        """
        if not date:
            return ""
        return datetime.strftime(fields.Date.to_date(date), "%d%m%Y")

    @api.model
    def get_html(self):
        """Render dynamic view from ir.action.client"""
        result = {}
        rcontext = {}
        rec = self.browse(self.env.context.get("active_id"))
        if rec:
            rcontext["o"] = rec
            result["html"] = self.env.ref(self.env.context.get("template_name")).render(
                rcontext
            )
        return result
