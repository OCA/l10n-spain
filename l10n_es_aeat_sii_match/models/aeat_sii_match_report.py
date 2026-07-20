# Copyright 2018 Studio73 - Abraham Anes
# Copyright 2019 Studio73 - Pablo Fuentes
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
from calendar import monthrange
from datetime import datetime

from zeep.helpers import serialize_object

from odoo import Command, api, exceptions, fields, models
from odoo.exceptions import UserError
from odoo.modules.registry import Registry

from odoo.addons.l10n_es_aeat.models.aeat_mixin import AEAT_DATE_FORMAT

SII_VERSION = "1.1"


class SiiMatchReport(models.Model):
    _name = "l10n.es.aeat.sii.match.report"
    _description = "AEAT SII match Report"

    name = fields.Char(string="Report identifier", required=True)
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("calculated", "Calculated"),
            ("done", "Done"),
            ("error", "Error"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
    )
    period_type = fields.Selection(
        selection=[
            ("01", "01 - January"),
            ("02", "02 - February"),
            ("03", "03 - March"),
            ("04", "04 - April"),
            ("05", "05 - May"),
            ("06", "06 - June"),
            ("07", "07 - July"),
            ("08", "08 - August"),
            ("09", "09 - September"),
            ("10", "10 - October"),
            ("11", "11 - November"),
            ("12", "12 - December"),
        ],
        string="Period type",
        required=True,
    )
    fiscalyear = fields.Integer(
        string="Fiscal year", required=True, default=fields.Date.today().year
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company.id,
        string="Company",
        required=True,
    )
    calculate_date = fields.Datetime(string="Calculate date")
    result_ids = fields.One2many(
        comodel_name="l10n.es.aeat.sii.match.result",
        inverse_name="report_id",
        string="SII Match Result",
        readonly=True,
    )
    invoice_type = fields.Selection(
        selection=[("out", "Out invoice/refund"), ("in", "In invoice/refund")],
        string="Invoice type",
        required=True,
    )
    number_records = fields.Integer(string="Total records", readonly=True)
    number_records_both = fields.Integer(
        string="Records in Odoo and SII", readonly=True
    )
    number_records_odoo = fields.Integer(string="Records only in Odoo", readonly=True)
    number_records_sii = fields.Integer(string="Records only in SII", readonly=True)
    number_records_correct = fields.Integer(
        string="Records correctly contrasted", readonly=True
    )
    number_records_no_exist = fields.Integer(
        string="Records without contrast", readonly=True
    )
    number_records_partially = fields.Integer(
        string="Records partially correct", readonly=True
    )
    number_records_no_test = fields.Integer(
        string="Records no testables", readonly=True
    )
    number_records_in_process = fields.Integer(
        string="Records in process of contrast", readonly=True
    )
    number_records_not_contrasted = fields.Integer(
        string="Records not contasted", readonly=True
    )
    number_records_partially_contrasted = fields.Integer(
        string="Records partially contrasted", readonly=True
    )
    number_records_contrasted = fields.Integer(
        string="Records contrasted", readonly=True
    )

    def _get_date_interval(self):
        """Obtain the starting and ending dates for the selected period type."""
        self.ensure_one()
        year = self.fiscalyear
        if self.period_type in ("1T", "2T", "3T", "4T"):
            # Trimestral
            starting_month = 1 + (int(self.period_type[0]) - 1) * 3
            ending_month = starting_month + 2
            date_start = fields.Date.to_date(f"{year}-{starting_month}-01")
            date_end = fields.Date.to_date(
                f"{year}-{ending_month}-{monthrange(year, ending_month)[1]}"
            )
        else:
            # Mensual
            month = int(self.period_type)
            date_start = fields.Date.to_date(f"{year}-{self.period_type}-01")
            date_end = fields.Date.to_date(
                f"{year}-{month}-{monthrange(year, month)[1]}"
            )
        return date_start, date_end

    def _get_invoice_dict(self):
        self.ensure_one()
        inv_dict = {
            "FiltroConsulta": {},
            "PeriodoLiquidacion": {
                "Ejercicio": str(self.fiscalyear),
                "Periodo": self.period_type,
            },
        }
        return inv_dict

    def _get_aeat_odoo_invoices_by_csv(self, sii_response):
        matched_invoices = {}
        left_invoices = []
        for invoice in sii_response:
            invoice = json.loads(json.dumps(serialize_object(invoice)))
            csv = invoice["DatosPresentacion"]["CSV"]
            invoice_state = invoice["EstadoFactura"]["EstadoRegistro"]
            odoo_invoice = self.env["account.move"].search([("sii_csv", "=", csv)])
            if odoo_invoice:
                matched_invoices[odoo_invoice] = invoice
            elif invoice_state != "Anulada":
                left_invoices.append(invoice)
        return matched_invoices, left_invoices

    def _get_aeat_odoo_invoices_by_num(self, left_invoices, matched_invoices):
        left_results = []
        for invoice in left_invoices:
            name = invoice["IDFactura"]["NumSerieFacturaEmisor"]
            if self.invoice_type == "out":
                odoo_invoice = self.env["account.move"].search(
                    [
                        "|",
                        ("name", "=", name),
                        ("thirdparty_number", "=", name),
                        ("move_type", "in", ["out_invoice", "out_refund"]),
                    ],
                    limit=1,
                )
            else:
                invoice_date = invoice["IDFactura"]["FechaExpedicionFacturaEmisor"]
                invoice_date = datetime.strptime(invoice_date, AEAT_DATE_FORMAT)
                odoo_invoice = self.env["account.move"].search(
                    [
                        ("ref", "=", name),
                        ("invoice_date", "=", invoice_date),
                        ("move_type", "in", ["in_invoice", "in_refund"]),
                    ],
                )
                if len(odoo_invoice) > 1:
                    vat = invoice["IDFactura"]["IDEmisorFactura"].get("NIF", "NO_VALID")
                    for rec in odoo_invoice:
                        if vat in rec.partner_id.vat:
                            odoo_invoice = rec
                            break
                    else:
                        odoo_invoice = False  # Don't match with any of them
            if odoo_invoice and odoo_invoice not in list(matched_invoices.keys()):
                matched_invoices[odoo_invoice] = invoice
            else:
                left_results.append(invoice)
        return matched_invoices, left_results

    def _get_aeat_odoo_invoices(self, sii_response):
        matched_invoices, left_invoices = self._get_aeat_odoo_invoices_by_csv(
            sii_response
        )
        matched_invoices, left_invoices = self._get_aeat_odoo_invoices_by_num(
            left_invoices, matched_invoices
        )
        res = []
        invoices_list = {}
        for odoo_document, invoice in list(matched_invoices.items()):
            vals = odoo_document._get_match_report_values(invoice)
            res.append(vals)
            invoices_list[odoo_document] = {
                "sii_match_return": vals.pop("sii_match_return"),
                "sii_match_state": vals["sii_match_state"],
                "sii_contrast_state": vals["sii_contrast_state"],
            }
        for invoice in left_invoices:
            # We call the method with empty record for getting the expected result
            vals = self.env["account.move"]._get_match_report_values(invoice)
            vals.pop("sii_match_return")
            res.append(vals)
        return res, invoices_list

    def _get_not_in_sii_invoices(self, invoices):
        self.ensure_one()
        date_start, date_end = self._get_date_interval()
        res = []
        inv_types = (
            ["out_invoice", "out_refund"]
            if self.invoice_type == "out"
            else ["in_invoice", "in_refund"]
        )
        prev_move_ids = [x.id for x in invoices.keys() if x._name == "account.move"]
        invoices = self.env["account.move"].search(
            [
                ("id", "not in", prev_move_ids),
                ("date", ">=", date_start),
                ("date", "<", date_end),
                ("company_id", "=", self.company_id.id),
                ("move_type", "in", inv_types),
                ("sii_enabled", "=", True),
                ("state", "=", "posted"),
            ]
        )
        for invoice in invoices:
            res.append(invoice._get_match_report_values(False))
        return res

    def _update_odoo_invoices(self, documents):
        self.ensure_one()
        for document, values in documents.items():
            document.write(values)

    def _get_match_result_values(self, sii_response):
        self.ensure_one()
        invoices, matched_invoices = self._get_aeat_odoo_invoices(sii_response)
        invoices += self._get_not_in_sii_invoices(matched_invoices)
        self._update_odoo_invoices(matched_invoices)
        summary = {
            "total": len(invoices),
            "both": len([i for i in invoices if i["invoice_location"] == "both"]),
            "sii": len([i for i in invoices if i["invoice_location"] == "sii"]),
            "odoo": len([i for i in invoices if i["invoice_location"] == "odoo"]),
            "correct": len(
                [i for i in invoices if i["sii_contrast_state"] == "correct"]
            ),
            "no_exist": len(
                [i for i in invoices if i["sii_contrast_state"] == "no_exist"]
            ),
            "partially": len(
                [i for i in invoices if i["sii_contrast_state"] == "partially"]
            ),
            "no_test": len(
                [
                    i
                    for i in invoices
                    if (i.get("sii_match_state", False) and i["sii_match_state"] == "1")
                ]
            ),
            "in_process": len(
                [
                    i
                    for i in invoices
                    if (i.get("sii_match_state", False) and i["sii_match_state"] == "2")
                ]
            ),
            "not_contrasted": len(
                [
                    i
                    for i in invoices
                    if (i.get("sii_match_state", False) and i["sii_match_state"] == "3")
                ]
            ),
            "partially_contrasted": len(
                [
                    i
                    for i in invoices
                    if (i.get("sii_match_state", False) and i["sii_match_state"] == "4")
                ]
            ),
            "contrasted": len(
                [
                    i
                    for i in invoices
                    if (i.get("sii_match_state", False) and i["sii_match_state"] == "5")
                ]
            ),
        }
        vals = [
            Command.create(i)
            for i in invoices
            if (i["sii_contrast_state"] != "correct" or i["sii_match_state"] == "4")
        ]
        return vals, summary

    def _get_invoices_from_sii(self):
        for sii_match_report in self.filtered(
            lambda r: r.state in ["draft", "error", "calculated"]
        ):
            mapping_key = "out_invoice"
            if sii_match_report.invoice_type == "in":
                mapping_key = "in_invoice"
            try:
                serv = (
                    self.env["account.move"]
                    .search(
                        [("company_id", "in", [self.company_id.id, False])], limit=1
                    )
                    ._connect_aeat(mapping_key)
                )
            except OSError as e:
                raise UserError(
                    self.env._("Error with AEAT certificates: %(error)s", error=e)
                ) from e
            header = sii_match_report._get_aeat_header()
            match_vals = {}
            summary = {}
            diffs = []
            try:
                inv_dict = sii_match_report._get_invoice_dict()
                if sii_match_report.invoice_type == "out":
                    res = serv.ConsultaLRFacturasEmitidas(header, inv_dict)
                    res_line = res["RegistroRespuestaConsultaLRFacturasEmitidas"]
                elif sii_match_report.invoice_type == "in":
                    res = serv.ConsultaLRFacturasRecibidas(header, inv_dict)
                    res_line = res["RegistroRespuestaConsultaLRFacturasRecibidas"]
                if res_line:
                    (diffs, summary) = sii_match_report._get_match_result_values(
                        res_line
                    )
                match_vals.update(
                    {
                        "number_records": summary.get("total", 0),
                        "number_records_both": summary.get("both", 0),
                        "number_records_odoo": summary.get("odoo", 0),
                        "number_records_sii": summary.get("sii", 0),
                        "number_records_correct": summary.get("correct", 0),
                        "number_records_no_exist": summary.get("no_exist", 0),
                        "number_records_partially": summary.get("partially", 0),
                        "number_records_no_test": summary.get("no_test", 0),
                        "number_records_in_process": summary.get("in_process", 0),
                        "number_records_not_contrasted": summary.get(
                            "not_contrasted", 0
                        ),
                        "number_records_partially_contrasted": summary.get(
                            "partially_contrasted", 0
                        ),
                        "number_records_contrasted": summary.get("contrasted", 0),
                    }
                )
                match_vals["result_ids"] = [Command.clear()] + diffs
                match_vals["state"] = "calculated"
                match_vals["calculate_date"] = fields.Datetime.now()
                sii_match_report.write(match_vals)
            except Exception:
                new_cr = Registry(self.env.cr.dbname).cursor()
                env = api.Environment(new_cr, self.env.uid, self.env.context)
                sii_match_report = env["l10n.es.aeat.sii.match.report"].browse(self.id)
                match_vals.update({"state": "error"})
                sii_match_report.write(match_vals)
                new_cr.commit()
                new_cr.close()
                raise

    def _get_aeat_header(self):
        """Builds SII send header

        :return Dict with header data depending on cancellation
        """
        self.ensure_one()
        company = self.company_id
        if not company.vat:
            raise exceptions.UserError(
                self.env._("No VAT configured for the company '%s'", company.name)
            )
        header = {
            "IDVersionSii": SII_VERSION,
            "Titular": {
                "NombreRazon": self.company_id.name[0:120],
                "NIF": self.company_id.partner_id._parse_aeat_vat_info()[2],
            },
        }
        return header

    def button_calculate(self):
        self._get_invoices_from_sii()

    def button_cancel(self):
        self.write({"state": "cancelled"})

    def button_recover(self):
        self.write({"state": "draft"})

    def button_confirm(self):
        self.write({"state": "done"})

    def open_result(self):
        self.ensure_one()
        tree_view = self.env.ref(
            "l10n_es_aeat_sii_match.view_l10n_es_aeat_sii_match_result_tree"
        )
        return {
            "name": self.env._("Results"),
            "view_mode": "list, form",
            "res_model": "l10n.es.aeat.sii.match.result",
            "views": [(tree_view and tree_view.id or False, "list"), (False, "form")],
            "type": "ir.actions.act_window",
            "domain": [("id", "in", self.result_ids.ids)],
            "context": {},
        }


class SiiMatchResult(models.Model):
    _name = "l10n.es.aeat.sii.match.result"
    _description = "AEAT SII Match - Result"
    _order = "invoice asc"

    @api.model
    def _get_selection_sii_match_state(self):
        return self.env["account.move"].fields_get(allfields=["sii_match_state"])[
            "sii_match_state"
        ]["selection"]

    report_id = fields.Many2one(
        comodel_name="l10n.es.aeat.sii.match.report",
        string="AEAT SII Match Report ID",
        ondelete="cascade",
    )
    invoice = fields.Char()
    invoice_id = fields.Many2oneReference(
        string="Document", model_field="model", readonly=True, index=True, required=True
    )
    # the default keeps the retro-compatibility
    model = fields.Char(default="account.move", required=True)
    csv = fields.Char(string="CSV")
    sii_match_state = fields.Selection(
        string="Match state",
        readonly=True,
        copy=False,
        selection="_get_selection_sii_match_state",
    )
    sii_contrast_state = fields.Selection(
        string="AEAT contrast state",
        readonly=True,
        copy=False,
        selection=[
            ("correct", "Correct"),
            ("no_exist", "Doesn't exist"),
            ("partially", "Partially correct"),
        ],
    )
    invoice_location = fields.Selection(
        string="Invoice location",
        readonly=True,
        copy=False,
        selection=[
            ("both", "Invoice in Odoo and SII"),
            ("odoo", "Invoice in Odoo"),
            ("sii", "Invoice in SII"),
        ],
    )
    sii_match_difference_ids = fields.One2many(
        string="SII match differences",
        readonly=True,
        copy=False,
        comodel_name="l10n.es.aeat.sii.match.difference",
        inverse_name="report_id",
    )
