# Copyright 2017 Praxya (http://praxya.com/)
#                Daniel Rodriguez Lijo <drl.9319@gmail.com>
# Copyright 2017 ForgeFlow, S.L. <contact@forgeflow.com>
# Copyright 2018 Luis M. Ontalba <luismaront@gmail.com>
# Copyright 2019 Tecnativa - Carlos Dauden
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0
import datetime
import re

from odoo import _, api, fields, models
from odoo.exceptions import Warning as UserError
from odoo.tools import ormcache


class L10nEsVatBook(models.Model):
    _name = "l10n.es.vat.book"
    _description = "Spanish VAT book report"
    _inherit = "l10n.es.aeat.report"
    _aeat_number = "LIVA"
    _period_yearly = True

    number = fields.Char(default="vat_book", readonly="True")

    line_ids = fields.One2many(
        comodel_name="l10n.es.vat.book.line",
        inverse_name="vat_book_id",
        string="Issued/Received invoices",
        copy=False,
        readonly="True",
    )

    issued_line_ids = fields.One2many(
        comodel_name="l10n.es.vat.book.line",
        inverse_name="vat_book_id",
        domain=[("line_type", "=", "issued")],
        string="Issued invoices",
        copy=False,
        readonly="True",
    )

    rectification_issued_line_ids = fields.One2many(
        comodel_name="l10n.es.vat.book.line",
        inverse_name="vat_book_id",
        domain=[("line_type", "=", "rectification_issued")],
        string="Issued Refund Invoices",
        copy=False,
        readonly="True",
    )

    received_line_ids = fields.One2many(
        comodel_name="l10n.es.vat.book.line",
        inverse_name="vat_book_id",
        domain=[("line_type", "=", "received")],
        string="Received invoices",
        copy=False,
        readonly="True",
    )

    rectification_received_line_ids = fields.One2many(
        comodel_name="l10n.es.vat.book.line",
        inverse_name="vat_book_id",
        domain=[("line_type", "=", "rectification_received")],
        string="Received Refund Invoices",
        copy=False,
        readonly="True",
    )

    calculation_date = fields.Date(string="Calculation Date")

    tax_summary_ids = fields.One2many(
        comodel_name="l10n.es.vat.book.tax.summary",
        string="Tax Summary",
        inverse_name="vat_book_id",
        readonly="True",
    )

    issued_tax_summary_ids = fields.One2many(
        comodel_name="l10n.es.vat.book.tax.summary",
        string="Issued Tax Summary",
        inverse_name="vat_book_id",
        domain=[("book_type", "=", "issued")],
        readonly="True",
    )

    received_tax_summary_ids = fields.One2many(
        comodel_name="l10n.es.vat.book.tax.summary",
        string="Received Tax Summary",
        inverse_name="vat_book_id",
        domain=[("book_type", "=", "received")],
        readonly="True",
    )

    summary_ids = fields.One2many(
        comodel_name="l10n.es.vat.book.summary",
        string="Summary",
        inverse_name="vat_book_id",
        readonly="True",
    )

    issued_summary_ids = fields.One2many(
        comodel_name="l10n.es.vat.book.summary",
        string="Issued Summary",
        inverse_name="vat_book_id",
        domain=[("book_type", "=", "issued")],
        readonly="True",
    )

    received_summary_ids = fields.One2many(
        comodel_name="l10n.es.vat.book.summary",
        string="Received Summary",
        inverse_name="vat_book_id",
        domain=[("book_type", "=", "received")],
        readonly="True",
    )

    auto_renumber = fields.Boolean(
        "Auto renumber invoices received", states={"draft": [("readonly", False)]}
    )

    @api.model
    def _prepare_vat_book_tax_summary(self, tax_lines, book_type):
        tax_summary_data_recs = {}
        for tax_line in tax_lines:
            if tax_line.tax_id not in tax_summary_data_recs:
                tax_summary_data_recs[tax_line.tax_id] = {
                    "book_type": book_type,
                    "base_amount": 0.0,
                    "tax_amount": 0.0,
                    "total_amount": 0.0,
                    "tax_id": tax_line.tax_id.id,
                    "vat_book_id": self.id,
                    "special_tax_group": tax_line.special_tax_group,
                }
            tax_summary_data_recs[tax_line.tax_id][
                "base_amount"
            ] += tax_line.base_amount
            tax_summary_data_recs[tax_line.tax_id]["tax_amount"] += tax_line.tax_amount
            tax_summary_data_recs[tax_line.tax_id][
                "total_amount"
            ] += tax_line.total_amount
        return tax_summary_data_recs

    @api.model
    def _create_vat_book_tax_summary(self, tax_summary_data_recs):
        return self.env["l10n.es.vat.book.tax.summary"].create(
            list(tax_summary_data_recs.values())
        )

    def _prepare_vat_book_summary(self, tax_summary_recs, book_type):
        vals_list = []
        total_dic = {}
        for line in tax_summary_recs:
            if line.special_tax_group not in total_dic:
                total_dic[line.special_tax_group] = {
                    "base_amount": line.base_amount,
                    "tax_amount": line.tax_amount,
                    "total_amount": line.total_amount,
                }
            else:
                total_group = total_dic[line.special_tax_group]
                total_group["base_amount"] += line.base_amount
                total_group["tax_amount"] += line.tax_amount
                total_group["total_amount"] += line.total_amount
        for key, total_group in total_dic.items():
            vals_list.append(
                {
                    "book_type": book_type,
                    "special_tax_group": key,
                    "base_amount": total_group["base_amount"],
                    "tax_amount": total_group["tax_amount"],
                    "total_amount": total_group["total_amount"],
                    "vat_book_id": self.id,
                }
            )
        return vals_list

    @api.model
    def _create_vat_book_summary(self, tax_summary_recs, book_type):
        return self.env["l10n.es.vat.book.summary"].create(
            self._prepare_vat_book_summary(tax_summary_recs, book_type)
        )

    def calculate(self):
        """
        Funcion call from vat_book
        """
        self._calculate_vat_book()
        return True

    def _prepare_book_line_vals(self, move_line, line_type):
        """
        This function make the dictionary to create a new record in issued
        invoices, Received invoices or rectification invoices

        Args:
            move_line (obj): move

        Returns:
            dictionary: Vals from the new record.
        """
        ref = move_line.ref
        ext_ref = ""
        invoice = move_line.move_id
        partner = move_line.partner_id
        if invoice:
            partner = invoice.commercial_partner_id
            ref = invoice.name
            ext_ref = invoice.ref
        return {
            "line_type": line_type,
            "invoice_date": move_line.date,
            "partner_id": partner.id,
            "vat_number": partner.vat,
            "move_id": invoice.id,
            "ref": ref,
            "external_ref": ext_ref,
            "vat_book_id": self.id,
            "tax_lines": {},
            "base_amount": 0.0,
            "special_tax_group": False,
        }

    def _prepare_book_line_tax_vals(self, move_line, vat_book_line):
        balance = move_line.credit - move_line.debit
        if vat_book_line["line_type"] in ["received", "rectification_received"]:
            balance = -balance
        base_amount_untaxed = (
            balance if move_line.tax_ids and not move_line.tax_line_id else 0.0
        )
        fee_amount_untaxed = balance if move_line.tax_line_id else 0.0
        return {
            "tax_id": move_line.tax_line_id.id,
            "base_amount": base_amount_untaxed,
            "tax_amount": fee_amount_untaxed,
            "total_amount": base_amount_untaxed + fee_amount_untaxed,
            "move_line_ids": [(4, move_line.id)],
            "special_tax_group": False,
        }

    def upsert_book_line_tax(self, move_line, vat_book_line, implied_taxes):
        vals = self._prepare_book_line_tax_vals(move_line, vat_book_line)
        tax_lines = vat_book_line["tax_lines"]
        implied_lines = []
        if move_line.tax_line_id:
            key = self.get_book_line_tax_key(move_line, move_line.tax_line_id)
            if key not in tax_lines:
                tax_lines[key] = vals.copy()
            else:
                tax_lines[key]["tax_amount"] += vals["tax_amount"]
                tax_lines[key]["total_amount"] += vals["total_amount"]
                tax_lines[key]["move_line_ids"] += vals["move_line_ids"]
            implied_lines.append(tax_lines[key])
        for i, tax in enumerate(move_line.tax_ids):
            if i == 0:
                vat_book_line["base_amount"] += vals["base_amount"]
            if tax not in implied_taxes:
                continue
            key = self.get_book_line_tax_key(move_line, tax)
            if key not in tax_lines:
                tax_lines[key] = vals.copy()
                tax_lines[key]["tax_id"] = tax.id
            else:
                tax_lines[key]["base_amount"] += vals["base_amount"]
                tax_lines[key]["total_amount"] += vals["total_amount"]
                # if i == 0:
                tax_lines[key]["move_line_ids"] += vals["move_line_ids"]
            implied_lines.append(tax_lines[key])
            sp_taxes_dic = self.get_special_taxes_dic()
            if tax.id in sp_taxes_dic:
                tax_group = sp_taxes_dic[tax.id]["special_tax_group"]
                vat_book_line["special_tax_group"] = tax_group
                tax_lines[key]["special_tax_group"] = tax_group
        if vat_book_line["special_tax_group"]:
            base_line = next(
                filter(lambda l: not l["special_tax_group"], implied_lines), None
            )
            special_line = next(
                filter(lambda l: l["special_tax_group"], implied_lines), None
            )
            if base_line and special_line:
                base_line.update(
                    {
                        "special_tax_id": special_line["tax_id"],
                        "special_tax_amount": special_line["tax_amount"],
                        "total_amount_special_include": base_line["total_amount"]
                        + special_line["tax_amount"],
                    }
                )

    def _clear_old_data(self):
        """
        This function clean all the old data to make a new calculation
        """
        self.line_ids.unlink()
        self.summary_ids.unlink()
        self.tax_summary_ids.unlink()

    def _account_move_line_domain(self, taxes):
        # search move lines that contain these tax codes
        return [
            ("date", ">=", self.date_start),
            ("date", "<=", self.date_end),
            "|",
            ("tax_ids", "in", taxes.ids),
            ("tax_line_id", "in", taxes.ids),
        ]

    def _get_account_move_lines(self, taxes):
        return self.env["account.move.line"].search(
            self._account_move_line_domain(taxes)
        )

    @ormcache("self.id")
    def get_pos_partner_ids(self):
        return (
            self.env["res.partner"]
            .with_context(active_test=False)
            .search([("aeat_anonymous_cash_customer", "=", True)])
            .ids
        )

    @ormcache("self.id")
    def get_special_taxes_dic(self):
        map_lines = self.env["aeat.vat.book.map.line"].search(
            [("special_tax_group", "!=", False)]
        )
        special_dic = {}
        for map_line in map_lines:
            for tax in self.get_taxes_from_templates(map_line.tax_tmpl_ids):
                special_dic[tax.id] = {
                    "name": map_line.name,
                    "book_type": map_line.book_type,
                    "special_tax_group": map_line.special_tax_group,
                    "fee_type_xlsx_column": map_line.fee_type_xlsx_column,
                    "fee_amount_xlsx_column": map_line.fee_amount_xlsx_column,
                }
        return special_dic

    def get_book_line_key(self, move_line):
        return move_line.move_id.id, move_line.move_id.id

    def get_book_line_tax_key(self, move_line, tax):
        return move_line.move_id.id, move_line.move_id.id, tax.id

    def _set_line_type(self, line_vals, line_type):
        if line_vals["base_amount"] < 0.0:
            line_vals["line_type"] = "rectification_{}".format(line_type)

    def _check_exceptions(self, line_vals):
        if (
            not line_vals["vat_number"]
            and line_vals["partner_id"] not in self.get_pos_partner_ids()
        ):
            line_vals["exception_text"] = _("Without VAT")

    def create_vat_book_lines(self, move_lines, line_type, taxes):
        VatBookLine = self.env["l10n.es.vat.book.line"]
        moves_dic = {}
        for move_line in move_lines:
            line_key = self.get_book_line_key(move_line)
            if line_key not in moves_dic:
                moves_dic[line_key] = self._prepare_book_line_vals(move_line, line_type)
            self.upsert_book_line_tax(move_line, moves_dic[line_key], taxes)
        lines_values = []
        for line_vals in moves_dic.values():
            tax_lines = line_vals.pop("tax_lines")
            tax_line_list = []
            tax_amount = 0.0
            for tax_line_vals in tax_lines.values():
                tax_amount += tax_line_vals["tax_amount"]
                tax_line_list.append((0, 0, tax_line_vals))
            self._set_line_type(line_vals, line_type)
            line_vals.update(
                {
                    "total_amount": line_vals["base_amount"] + tax_amount,
                    "tax_line_ids": [(0, 0, vals) for vals in tax_lines.values()],
                }
            )
            self._check_exceptions(line_vals)
            lines_values.append(line_vals)
        VatBookLine.create(lines_values)

    def _calculate_vat_book(self):
        """
        This function calculate all the taxes, from issued invoices,
        received invoices and rectification invoices
        """
        for rec in self:
            if not rec.company_id.partner_id.vat:
                raise UserError(_("This company doesn't have VAT"))

            # clean the old records
            rec._clear_old_data()

            tax_templates = (
                self.env["aeat.vat.book.map.line"].search([]).mapped("tax_tmpl_ids")
            )
            taxes_issued = self.get_taxes_from_templates(
                tax_templates.filtered(lambda t: t.type_tax_use == "sale")
            )
            taxes_received = self.get_taxes_from_templates(
                tax_templates.filtered(lambda t: t.type_tax_use == "purchase")
            )

            # Get all the account move lines that contain VAT that is
            #  applicable to this report.
            lines_issued = rec._get_account_move_lines(taxes_issued)
            self.create_vat_book_lines(lines_issued, "issued", taxes_issued)
            lines_received = rec._get_account_move_lines(taxes_received)
            self.create_vat_book_lines(lines_received, "received", taxes_received)

            # Issued
            book_type = "issued"
            issued_tax_lines = rec.issued_line_ids.mapped("tax_line_ids")
            rectification_issued_tax_lines = rec.rectification_issued_line_ids.mapped(
                "tax_line_ids"
            )
            tax_summary_data_recs = rec._prepare_vat_book_tax_summary(
                issued_tax_lines + rectification_issued_tax_lines, book_type
            )
            rec._create_vat_book_tax_summary(tax_summary_data_recs)
            rec._create_vat_book_summary(rec.issued_tax_summary_ids, book_type)

            # Received
            book_type = "received"
            received_tax_lines = rec.received_line_ids.mapped("tax_line_ids")
            # flake8: noqa
            rectification_received_tax_lines = (
                rec.rectification_received_line_ids.mapped("tax_line_ids")
            )
            tax_summary_data_recs = rec._prepare_vat_book_tax_summary(
                received_tax_lines + rectification_received_tax_lines, book_type
            )
            rec._create_vat_book_tax_summary(tax_summary_data_recs)
            rec._create_vat_book_summary(rec.received_tax_summary_ids, book_type)

            # If we require to auto-renumber invoices received
            if rec.auto_renumber:
                rec_invs = self.env["l10n.es.vat.book.line"].search(
                    [("vat_book_id", "=", rec.id), ("line_type", "=", "received")],
                    order="invoice_date asc, ref asc",
                )
                i = 1
                for rec_inv in rec_invs:
                    rec_inv.entry_number = i
                    i += 1
                rec_invs = self.env["l10n.es.vat.book.line"].search(
                    [
                        ("vat_book_id", "=", rec.id),
                        ("line_type", "=", "rectification_received"),
                    ],
                    order="invoice_date asc, ref asc",
                )
                i = 1
                for rec_inv in rec_invs:
                    rec_inv.entry_number = i
                    i += 1
                # Write state and date in the report
            rec.write(
                {"state": "calculated", "calculation_date": fields.Datetime.now()}
            )

    def view_issued_invoices(self):
        self.ensure_one()
        report_name = "l10n_es_vat_book.report_vat_book_invoices_issued_html"
        return (
            self.env["ir.actions.report"]
            .search(
                [("report_name", "=", report_name), ("report_type", "=", "qweb-html")],
                limit=1,
            )
            .report_action(self.ids)
        )

    def view_received_invoices(self):
        self.ensure_one()
        report_name = "l10n_es_vat_book.report_vat_book_invoices_received_html"
        return (
            self.env["ir.actions.report"]
            .search(
                [("report_name", "=", report_name), ("report_type", "=", "qweb-html")],
                limit=1,
            )
            .report_action(self.ids)
        )

    def _format_date(self, date):
        # format date following user language
        lang_model = self.env["res.lang"]
        lang = lang_model._lang_get(self.env.user.lang)
        date_format = lang.date_format
        return datetime.datetime.strftime(fields.Date.to_date(date), date_format)

    def get_report_file_name(self):
        return "{}{}C{}".format(
            self.year, self.company_vat, re.sub(r"[\W_]+", "", self.company_id.name)
        )

    def button_confirm(self):
        if any(l.exception_text for l in self.line_ids):
            raise UserError(_("This book has warnings. Fix it before confirm"))
        return super().button_confirm()

    def export_xlsx(self):
        self.ensure_one()
        return self.env.ref("l10n_es_vat_book.l10n_es_vat_book_xlsx").report_action(
            self
        )
