# Copyright 2004-2011 Pexego Sistemas Informáticos. (http://pexego.es)
# Copyright 2012 NaN·Tic  (http://www.nan-tic.com)
# Copyright 2013 Acysos (http://www.acysos.com)
# Copyright 2013 Joaquín Pedrosa Gutierrez (http://gutierrezweb.es)
# Copyright 2016 Tecnativa - Antonio Espinosa
# Copyright 2016 Tecnativa - Angel Moya <odoo@tecnativa.com>
# Copyright 2018 PESOL - Angel Moya <info@pesol.es>
# Copyright 2019 Tecnativa - Carlos Dauden
# Copyright 2014-2022 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime
from calendar import monthrange

from odoo import _, api, exceptions, fields, models

KEY_TAX_MAPPING = {
    "A": "l10n_es_aeat_mod347.aeat_mod347_map_a",
    "B": "l10n_es_aeat_mod347.aeat_mod347_map_b",
}


class L10nEsAeatMod347Report(models.Model):
    _inherit = "l10n.es.aeat.report"
    _name = "l10n.es.aeat.mod347.report"
    _description = "AEAT 347 Report"
    _period_yearly = True
    _period_quarterly = False
    _period_monthly = False
    _aeat_number = "347"

    @api.depends(
        "partner_record_ids",
        "partner_record_ids.amount",
        "partner_record_ids.cash_amount",
        "partner_record_ids.real_estate_transmissions_amount",
    )
    def _compute_totals(self):
        """Calculates the total_* fields from the line values."""
        for record in self:
            record.total_partner_records = len(record.partner_record_ids)
            record.total_amount = sum(record.mapped("partner_record_ids.amount"))
            record.total_cash_amount = sum(
                record.mapped("partner_record_ids.cash_amount")
            )
            record.total_real_estate_transmissions_amount = sum(
                record.mapped("partner_record_ids.real_estate_transmissions_amount")
            )

    @api.depends("real_estate_record_ids", "real_estate_record_ids.amount")
    def _compute_totals_real_estate(self):
        """Calculates the total_* fields from the line values."""
        for record in self:
            record.total_real_estate_records = len(record.real_estate_record_ids)
            record.total_real_estate_amount = sum(
                record.mapped("real_estate_record_ids.amount")
            )

    number = fields.Char(default="347")
    operations_limit = fields.Float(
        string="Invoiced Limit (1)",
        digits="Account",
        default=3005.06,
        help="The declaration will include partners with the total of "
        "operations over this limit",
    )
    received_cash_limit = fields.Float(
        string="Received cash Limit (2)",
        digits="Account",
        default=6000.00,
        help="The declaration will show the total of cash operations over "
        "this limit",
    )
    total_partner_records = fields.Integer(
        compute="_compute_totals",
        string="Partners records",
        store=True,
    )
    total_amount = fields.Float(
        compute="_compute_totals",
        string="Amount",
        store=True,
    )
    total_cash_amount = fields.Float(
        compute="_compute_totals",
        string="Cash Amount",
        store=True,
    )
    total_real_estate_transmissions_amount = fields.Float(
        compute="_compute_totals",
        string="Real Estate Transmissions Amount",
        store=True,
    )
    total_real_estate_records = fields.Integer(
        compute="_compute_totals_real_estate",
        string="Real estate records",
        store=True,
    )
    total_real_estate_amount = fields.Float(
        compute="_compute_totals_real_estate",
        string="Real Estate Amount",
        store=True,
    )
    partner_record_ids = fields.One2many(
        comodel_name="l10n.es.aeat.mod347.partner_record",
        inverse_name="report_id",
        string="Partner Records",
    )
    real_estate_record_ids = fields.One2many(
        comodel_name="l10n.es.aeat.mod347.real_estate_record",
        inverse_name="report_id",
        string="Real Estate Records",
    )

    def _error_count(self, model):
        records_error_group = self.env["l10n.es.aeat.mod347.%s" % model].read_group(
            domain=[("check_ok", "=", False), ("report_id", "in", self.ids)],
            fields=["report_id"],
            groupby=["report_id"],
        )
        return {
            rec["report_id"][0]: rec["report_id_count"] for rec in records_error_group
        }

    def _compute_error_count(self):
        ret_val = super()._compute_error_count()
        partner_records_error_dict = self._error_count("partner_record")
        real_estate_record_error_dict = self._error_count("real_estate_record")

        for report in self:
            report.error_count += partner_records_error_dict.get(
                report.id, 0
            ) + real_estate_record_error_dict.get(report.id, 0)
        return ret_val

    def button_confirm(self):
        """Different check out in report"""
        for item in self:
            # Browse partner record lines to check if all are correct (all
            # fields filled)
            partner_errors = []
            for partner_record in item.partner_record_ids:
                if not partner_record.check_ok:
                    partner_errors.append(
                        _(
                            "- %(name)s %(id)s",
                            name=partner_record.partner_id.name,
                            id=partner_record.partner_id.id,
                        )
                    )
            real_state_errors = []
            for real_estate_record in item.real_estate_record_ids:
                if not real_estate_record.check_ok:
                    real_state_errors.append(
                        _(
                            "- %(name)s %(id)s",
                            name=real_estate_record.partner_id.name,
                            id=real_estate_record.partner_id.id,
                        )
                    )
            error = _(
                "Please review partner and real estate records, "
                "some of them are in red color:\n\n"
            )
            if partner_errors:
                error += _("Partner record errors:\n")
                error += "\n".join(partner_errors)
                error += "\n\n"
            if real_state_errors:
                error += _("Real estate record errors:\n")
                error += "\n".join(real_state_errors)
            if partner_errors or real_state_errors:
                raise exceptions.ValidationError(error)
        return super(L10nEsAeatMod347Report, self).button_confirm()

    def button_send_mails(self):
        self.partner_record_ids.filtered(
            lambda x: x.state == "pending"
        ).send_email_direct()

    def btn_list_records(self):
        return {
            "domain": "[('report_id','in'," + str(self.ids) + ")]",
            "name": _("Partner records"),
            "view_mode": "tree,form",
            "res_model": "l10n.es.aeat.mod347.partner_record",
            "type": "ir.actions.act_window",
        }

    def _account_move_line_domain(self, taxes):
        """Return domain for searching move lines.

        :param: taxes: Taxes to look for in move lines.
        """
        return [
            ("partner_id.not_in_mod347", "=", False),
            ("move_id.not_in_mod347", "=", False),
            ("date", ">=", self.date_start),
            ("date", "<=", self.date_end),
            "|",
            ("tax_ids", "in", taxes.ids),
            ("tax_line_id", "in", taxes.ids),
            ("parent_state", "=", "posted"),
        ]

    @api.model
    def _get_taxes(self, map_rec):
        """Obtain all the taxes to be considered for 347."""
        self.ensure_one()
        tax_templates = map_rec.mapped("tax_ids")
        if not tax_templates:
            raise exceptions.UserError(_("No Tax Mapping was found"))
        return self.get_taxes_from_templates(tax_templates)

    @api.model
    def _get_partner_347_identification(self, partner):
        country_code, _, vat = partner._parse_aeat_vat_info()
        if country_code == "ES":
            return {
                "partner_vat": vat,
                # Odoo Spanish states codes use car license plates approach
                # (CR, A, M...), instead of ZIP (01, 02...), so we need to
                # convert them, but fallbacking in existing one if not found.
                "partner_state_code": self.SPANISH_STATES.get(
                    partner.state_id.code, partner.state_id.code
                ),
                "partner_country_code": country_code,
            }
        else:
            return {
                "community_vat": vat,
                "partner_state_code": 99,
                "partner_country_code": country_code,
            }

    def _create_partner_records(self, key, map_ref, partner_record=None):
        sign = -1 if key == "B" else 1
        partner_record_obj = self.env["l10n.es.aeat.mod347.partner_record"]
        partner_obj = self.env["res.partner"]
        map_line = self.env.ref(map_ref)
        taxes = self._get_taxes(map_line)
        domain = self._account_move_line_domain(taxes)
        if partner_record:
            domain += [("partner_id", "=", partner_record.partner_id.id)]
        groups = self.env["account.move.line"].read_group(
            domain,
            ["partner_id", "balance"],
            ["partner_id"],
        )
        filtered_groups = list(
            filter(lambda d: abs(d["balance"]) > self.operations_limit, groups)
        )
        for group in filtered_groups:
            partner = partner_obj.browse(group["partner_id"][0])
            vals = {
                "report_id": self.id,
                "partner_id": partner.id,
                "representative_vat": "",
                "operation_key": key,
                "amount": sign * group["balance"],
            }
            vals.update(self._get_partner_347_identification(partner))
            move_groups = self.env["account.move.line"].read_group(
                group["__domain"],
                ["move_id", "balance"],
                ["move_id"],
            )
            vals["move_record_ids"] = [
                (
                    0,
                    0,
                    {
                        "move_id": move_group["move_id"][0],
                        "amount": sign * move_group["balance"],
                    },
                )
                for move_group in move_groups
            ]
            if partner_record:
                vals["move_record_ids"][0:0] = [
                    (2, x) for x in partner_record.move_record_ids.ids
                ]
                partner_record.write(vals)
            else:
                partner_record_obj.create(vals)

    def _create_cash_moves(self):
        partner_obj = self.env["res.partner"]
        move_line_obj = self.env["account.move.line"]
        cash_journals = self.env["account.journal"].search(
            [("type", "=", "cash")],
        )
        if not cash_journals:
            return
        domain = [
            ("account_id.account_type", "=", "asset_receivable"),
            ("journal_id", "in", cash_journals.ids),
            ("date", ">=", self.date_start),
            ("date", "<=", self.date_end),
            ("partner_id.not_in_mod347", "=", False),
        ]
        cash_groups = move_line_obj.read_group(
            domain, ["partner_id", "balance"], ["partner_id"]
        )
        for cash_group in cash_groups:
            partner = partner_obj.browse(cash_group["partner_id"][0])
            partner_record_obj = self.env["l10n.es.aeat.mod347.partner_record"]
            amount = abs(cash_group["balance"])
            if amount > self.received_cash_limit:
                move_lines = move_line_obj.search(cash_group["__domain"])
                partner_record = partner_record_obj.search(
                    [
                        ("partner_id", "=", partner.id),
                        ("operation_key", "=", "B"),
                        ("report_id", "=", self.id),
                    ]
                )
                if partner_record:
                    partner_record.write(
                        {
                            "cash_record_ids": [(6, 0, move_lines.ids)],
                            "cash_amount": amount,
                        }
                    )
                else:
                    vals = {
                        "report_id": self.id,
                        "partner_id": partner.id,
                        "representative_vat": "",
                        "operation_key": "B",
                        "amount": 0,
                        "cash_amount": amount,
                        "cash_record_ids": [(6, 0, move_lines.ids)],
                    }
                    vals.update(self._get_partner_347_identification(partner))
                    partner_record_obj.create(vals)

    def calculate(self):
        for report in self:
            # Delete previous partner records
            report.partner_record_ids.unlink()
            with self.env.norecompute():
                self._create_partner_records("A", KEY_TAX_MAPPING["A"])
                self._create_partner_records("B", KEY_TAX_MAPPING["B"])
                self._create_cash_moves()
            self.env.flush_all()
            report.partner_record_ids.calculate_quarter_totals()
        return True


class L10nEsAeatMod347PartnerRecord(models.Model):
    _name = "l10n.es.aeat.mod347.partner_record"
    _inherit = ["mail.thread", "mail.activity.mixin", "portal.mixin"]
    _description = "Partner Record"
    _rec_name = "partner_vat"
    _order = "check_ok asc,id"

    @api.model
    def _default_record_id(self):
        return self.env.context.get("report_id", False)

    report_id = fields.Many2one(
        comodel_name="l10n.es.aeat.mod347.report",
        string="AEAT 347 Report",
        ondelete="cascade",
        default=_default_record_id,
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Salesperson",
        tracking=True,
        default=lambda self: self.env.user,
        copy=False,
    )
    state = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("sent", "Sent"),
            ("confirmed", "Confirmed"),
            ("exception", "Exception"),
        ],
        default="pending",
    )
    operation_key = fields.Selection(
        selection=[
            (
                "A",
                "A - Adquisiciones de bienes y servicios superiores al " "límite (1)",
            ),
            ("B", "B - Entregas de bienes y servicios superiores al límite (1)"),
            ("C", "C - Cobros por cuenta de terceros superiores al límite (3)"),
            (
                "D",
                "D - Adquisiciones efectuadas por Entidades Públicas "
                "(...) superiores al límite (1)",
            ),
            (
                "E",
                "E - Subvenciones, auxilios y ayudas satisfechas por Ad. "
                "Públicas superiores al límite (1)",
            ),
            ("F", "F - Ventas agencia viaje"),
            ("G", "G - Compras agencia viaje"),
        ],
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner", string="Partner", required=True
    )
    partner_vat = fields.Char(string="VAT number", size=9)
    representative_vat = fields.Char(
        string="L.R. VAT number", size=9, help="Legal Representative VAT number"
    )
    community_vat = fields.Char(
        string="Community vat number",
        size=17,
        help="VAT number for professionals established in other state "
        "member without national VAT",
    )
    partner_country_code = fields.Char(string="Country Code", size=2)
    partner_state_code = fields.Char(string="State Code", size=2)
    first_quarter = fields.Float(
        string="First quarter operations",
        digits="Account",
        help="Total amount of first quarter in, out and refund invoices "
        "for this partner",
        tracking=True,
    )
    first_quarter_real_estate_transmission = fields.Float(
        string="First quarter real estate",
        digits="Account",
        help="Total amount of first quarter real estate transmissions "
        "for this partner",
    )
    second_quarter = fields.Float(
        string="Second quarter operations",
        digits="Account",
        help="Total amount of second quarter in, out and refund invoices "
        "for this partner",
        tracking=True,
    )
    second_quarter_real_estate_transmission = fields.Float(
        string="Second quarter real estate",
        digits="Account",
        help="Total amount of second quarter real estate transmissions "
        "for this partner",
    )
    third_quarter = fields.Float(
        string="Third quarter operations",
        digits="Account",
        help="Total amount of third quarter in, out and refund invoices "
        "for this partner",
        tracking=True,
    )
    third_quarter_real_estate_transmission = fields.Float(
        string="Third quarter real estate",
        digits="Account",
        help="Total amount of third quarter real estate transmissions "
        "for this partner",
    )
    fourth_quarter = fields.Float(
        string="Fourth quarter operations",
        digits="Account",
        help="Total amount of fourth quarter in, out and refund invoices "
        "for this partner",
        tracking=True,
    )
    fourth_quarter_real_estate_transmission = fields.Float(
        string="Fourth quarter real estate",
        digits="Account",
        help="Total amount of fourth quarter real estate transmissions "
        "for this partner",
    )
    amount = fields.Float(
        string="Operations amount",
        digits="Account",
        tracking=True,
    )
    cash_amount = fields.Float(
        string="Received cash amount",
        digits="Account",
    )
    real_estate_transmissions_amount = fields.Float(
        string="Real Estate Transmisions amount",
        digits="Account",
    )
    insurance_operation = fields.Boolean(
        help="Only for insurance companies. Set to identify insurance "
        "operations aside from the rest.",
    )
    cash_basis_operation = fields.Boolean(
        help="Only for cash basis operations. Set to identify cash basis "
        "operations aside from the rest.",
    )
    tax_person_operation = fields.Boolean(
        help="Only for taxable person operations. Set to identify taxable "
        "person operations aside from the rest.",
    )
    related_goods_operation = fields.Boolean(
        help="Only for related goods operations. Set to identify related "
        "goods operations aside from the rest.",
    )
    bussiness_real_estate_rent = fields.Boolean(
        help="Set to identify real estate rent operations aside from the rest."
        " You'll need to fill in the real estate info only when you are "
        "the one that receives the money.",
    )
    origin_year = fields.Integer(
        help="Origin cash operation year",
    )
    move_record_ids = fields.One2many(
        comodel_name="l10n.es.aeat.mod347.move.record",
        inverse_name="partner_record_id",
        string="Move records",
    )
    cash_record_ids = fields.Many2many(
        comodel_name="account.move.line",
        string="Cash payments",
        readonly=True,
    )
    check_ok = fields.Boolean(
        compute="_compute_check_ok",
        string="Record is OK",
        store=True,
        help="Checked if this record is OK",
    )
    error_text = fields.Char(compute="_compute_check_ok", store=True)

    @api.depends(
        "partner_country_code", "partner_state_code", "partner_vat", "community_vat"
    )
    def _compute_check_ok(self):
        for record in self:
            errors = []
            if not record.partner_country_code:
                errors.append(_("Without country code"))
            if not record.partner_state_code:
                errors.append(_("Without state code"))
            if record.partner_state_code and not record.partner_state_code.isdigit():
                errors.append(_("State code can only contain digits"))
            if not (record.partner_vat or record.partner_country_code != "ES"):
                errors.append(_("VAT must be defined for Spanish Contacts"))
            record.check_ok = not bool(errors)
            record.error_text = ", ".join(errors)

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        """Loads some partner data when the selected partner changes."""
        if self.partner_id:
            self.update(self.report_id._get_partner_347_identification(self.partner_id))

    @api.depends("move_record_ids.move_id.date", "report_id.year")
    def calculate_quarter_totals(self):
        def calc_amount_by_quarter(records, year, month_start):
            day_start = 1
            month_end = month_start + 2
            day_end = monthrange(year, month_end)[1]
            date_start = datetime.date(year, month_start, day_start)
            date_end = datetime.date(year, month_end, day_end)
            return sum(
                records.filtered(
                    lambda x: date_start <= x.move_id.date <= date_end
                ).mapped("amount")
            )

        for record in self:
            year = record.report_id.year
            moves = record.move_record_ids
            record.first_quarter = calc_amount_by_quarter(moves, year, 1)
            record.second_quarter = calc_amount_by_quarter(moves, year, 4)
            record.third_quarter = calc_amount_by_quarter(moves, year, 7)
            record.fourth_quarter = calc_amount_by_quarter(moves, year, 10)

    def action_exception(self):
        self.write({"state": "exception"})

    def get_confirm_url(self):
        self.ensure_one()
        return self._notify_get_action_link("controller", controller="/mod347/accept")

    def get_reject_url(self):
        self.ensure_one()
        return self._notify_get_action_link("controller", controller="/mod347/reject")

    def action_confirm(self):
        self.write({"state": "confirmed"})

    def action_send(self):
        self.write({"state": "sent"})
        self.ensure_one()
        template = self.env.ref("l10n_es_aeat_mod347.email_template_347")
        compose_form = self.env.ref("mail.email_compose_message_wizard_form")
        ctx = dict(
            default_model=self._name,
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode="comment",
            mark_invoice_as_sent=True,
        )
        return {
            "name": _("Compose Email"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "views": [(compose_form.id, "form")],
            "view_id": compose_form.id,
            "target": "new",
            "context": ctx,
        }

    def button_print(self):
        return self.env.ref("l10n_es_aeat_mod347.347_partner").report_action(self)

    def button_recompute(self):
        self.ensure_one()
        if self.operation_key not in ("A", "B"):
            return
        self.report_id._create_partner_records(
            self.operation_key,
            KEY_TAX_MAPPING[self.operation_key],
            partner_record=self,
        )
        self.calculate_quarter_totals()
        self.action_pending()

    def send_email_direct(self):
        template = self.env.ref("l10n_es_aeat_mod347.email_template_347")
        for record in self:
            template.send_mail(record.id)
        self.write({"state": "sent"})

    def action_pending(self):
        self.write({"state": "pending"})

    def message_get_suggested_recipients(self):
        """Add the invoicing partner to the suggested recipients sending an
        email.
        """
        recipients = super().message_get_suggested_recipients()
        partner_obj = self.env["res.partner"]
        for record in self:
            partner = partner_obj.browse(
                record.partner_id.address_get(["invoice"])["invoice"]
            )
            record._message_add_suggested_recipient(
                recipients,
                partner=partner,
            )
        return recipients


class L10nEsAeatMod347RealStateRecord(models.Model):
    _name = "l10n.es.aeat.mod347.real_estate_record"
    _description = "Real Estate Record"
    _rec_name = "reference"
    _order = "check_ok asc,id"

    @api.model
    def _default_record_id(self):
        return self.env.context.get("report_id", False)

    @api.model
    def _default_representative_vat(self):
        return self.env.context.get("representative_vat", False)

    report_id = fields.Many2one(
        comodel_name="l10n.es.aeat.mod347.report",
        string="AEAT 347 Report",
        ondelete="cascade",
        index=1,
        default=_default_record_id,
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        required=True,
    )
    partner_vat = fields.Char(
        string="VAT number",
        size=32,
    )
    representative_vat = fields.Char(
        string="L.R. VAT number",
        size=32,
        default=_default_representative_vat,
        help="Legal Representative VAT number",
    )
    amount = fields.Float(digits="Account")
    situation = fields.Selection(
        selection=[
            ("1", "1 - Spain but Basque Country and Navarra"),
            ("2", "2 - Basque Country and Navarra"),
            ("3", "3 - Spain, without catastral reference"),
            ("4", "4 - Foreign"),
        ],
        string="Real estate Situation",
        required=True,
    )
    reference = fields.Char(string="Catastral Reference", size=25)
    address_type = fields.Char(size=5)
    address = fields.Char(size=50)
    number_type = fields.Selection(
        selection=[("NUM", "Number"), ("KM.", "Kilometer"), ("S/N", "Without number")],
    )
    number = fields.Integer()
    number_calification = fields.Selection(
        selection=[("BIS", "Bis"), ("MOD", "Mod"), ("DUP", "Dup"), ("ANT", "Ant")],
    )
    block = fields.Char(size=3)
    portal = fields.Char(size=3)
    stairway = fields.Char(size=3)
    floor = fields.Char(size=3)
    door = fields.Char(size=3)
    complement = fields.Char(
        size=40,
        help="Complement (urbanization, industrial park...)",
    )
    city = fields.Char(size=30)
    township = fields.Char(size=30)
    township_code = fields.Char(size=5)
    state_code = fields.Char(size=2)
    postal_code = fields.Char(size=5)
    check_ok = fields.Boolean(
        compute="_compute_check_ok",
        string="Record is OK",
        store=True,
        help="Checked if this record is OK",
    )
    error_text = fields.Char(string="Errors", compute="_compute_check_ok", store=True)

    @api.depends("state_code")
    def _compute_check_ok(self):
        for record in self:
            errors = []
            if not record.state_code:
                errors.append(_("Without state code"))
            record.check_ok = not bool(errors)
            record.error_text = ", ".join(errors)

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        """Loads some partner data when the selected partner changes."""
        if self.partner_id:
            vals = self.report_id._get_partner_347_identification(self.partner_id)
            self.update(
                {
                    "partner_vat": vals.pop("partner_vat"),
                    "state_code": vals.pop("partner_state_code"),
                }
            )


class L10nEsAeatMod347MoveRecord(models.Model):
    _name = "l10n.es.aeat.mod347.move.record"
    _description = "Move Record"

    @api.model
    def _default_partner_record(self):
        return self.env.context.get("partner_record_id", False)

    partner_record_id = fields.Many2one(
        comodel_name="l10n.es.aeat.mod347.partner_record",
        string="Partner record",
        required=True,
        ondelete="cascade",
        index=True,
        default=_default_partner_record,
    )
    move_id = fields.Many2one(
        comodel_name="account.move",
        string="Invoice / Journal entry",
        ondelete="restrict",
    )
    date = fields.Date(
        string="Date",
        related="move_id.date",
        store=True,
        readonly=True,
    )
    amount = fields.Float(
        readonly=True,
    )
