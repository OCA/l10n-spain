# Copyright 2018 Studio73 - Abraham Anes
# Copyright 2019 Studio73 - Pablo Fuentes
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import copy
import json

from dateutil.relativedelta import relativedelta
from zeep.helpers import serialize_object

from odoo import _, api, exceptions, fields, models
from odoo.modules.registry import Registry

SII_VERSION = "1.1"


class SiiMatchReport(models.Model):
    _name = "l10n.es.aeat.sii.match.report"
    _description = "AEAT SII match Report"

    name = fields.Char(
        string="Report identifier",
        required=True,
    )
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
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    fiscalyear = fields.Integer(
        string="Fiscal year",
        required=True,
        default=fields.Date.today().year,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company.id,
        string="Company",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    calculate_date = fields.Datetime(
        string="Calculate date",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    sii_match_result = fields.One2many(
        comodel_name="l10n.es.aeat.sii.match.result",
        inverse_name="report_id",
        string="SII Match Result",
        readonly=True,
    )
    invoice_type = fields.Selection(
        selection=[("out", "Out invoice/refund"), ("in", "In invoice/refund")],
        string="Invoice type",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    number_records = fields.Integer(string="Total records", readonly=True)
    number_records_both = fields.Integer(
        string="Records in Odoo and SII",
        readonly=True,
    )
    number_records_odoo = fields.Integer(
        string="Records only in Odoo",
        readonly=True,
    )
    number_records_sii = fields.Integer(
        string="Records only in SII",
        readonly=True,
    )
    number_records_correct = fields.Integer(
        string="Records correctly contrasted",
        readonly=True,
    )
    number_records_no_exist = fields.Integer(
        string="Records without contrast",
        readonly=True,
    )
    number_records_partially = fields.Integer(
        string="Records partially contrasted",
        readonly=True,
    )
    number_records_no_test = fields.Integer(
        string="Records no testables",
        readonly=True,
    )
    number_records_in_process = fields.Integer(
        string="Records in process of contrast",
        readonly=True,
    )
    number_records_not_contrasted = fields.Integer(
        string="Records not contasted",
        readonly=True,
    )
    number_records_partially_contrasted = fields.Integer(
        string="Records partially contrasted",
        readonly=True,
    )
    number_records_contrasted = fields.Integer(
        string="Records contrasted",
        readonly=True,
    )
    sii_match_jobs_ids = fields.Many2many(
        comodel_name="queue.job",
        column1="sii_match_id",
        column2="job_id",
        string="Connector Jobs",
        copy=False,
    )

    def _process_invoices_from_sii(self):
        queue_obj = self.env["queue.job"].sudo()
        for item in self:
            item = item.sudo().with_company(item.company_id)
            new_delay = item.with_delay(eta=False).get_invoice_aeat()
            jb = queue_obj.search([("uuid", "=", new_delay.uuid)], limit=1)
            item.sii_match_jobs_ids |= jb

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
                matched_invoices[odoo_invoice.id] = invoice
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
                odoo_invoice = self.env["account.move"].search(
                    [
                        ("ref", "=", name),
                        ("move_type", "in", ["in_invoice", "in_refund"]),
                    ],
                    limit=1,
                )
            if odoo_invoice and odoo_invoice.id not in list(matched_invoices.keys()):
                matched_invoices[odoo_invoice.id] = invoice
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
        for odoo_inv_id, invoice in list(matched_invoices.items()):
            name = invoice["IDFactura"]["NumSerieFacturaEmisor"]
            csv = invoice["DatosPresentacion"]["CSV"]
            match_state = invoice["EstadoFactura"]["EstadoCuadre"]
            odoo_invoice = self.env["account.move"].browse([odoo_inv_id])
            inv_location = "both"
            contrast_state = "correct"
            diffs = odoo_invoice._get_diffs_values(invoice)
            if diffs:
                contrast_state = "partially"
            invoices_list[odoo_invoice.id] = {
                "sii_match_return": json.dumps(str(invoice), indent=4),
                "sii_match_state": match_state,
                "sii_contrast_state": contrast_state,
                "sii_match_difference_ids": copy.deepcopy(diffs),
            }
            res.append(
                {
                    "invoice": name,
                    "invoice_id": odoo_invoice.id,
                    "csv": csv,
                    "invoice_location": inv_location,
                    "sii_match_difference_ids": diffs,
                    "sii_match_state": match_state,
                    "sii_contrast_state": contrast_state,
                }
            )
        for invoice in left_invoices:
            name = invoice["IDFactura"]["NumSerieFacturaEmisor"]
            csv = invoice["DatosPresentacion"]["CSV"]
            match_state = invoice["EstadoFactura"]["EstadoCuadre"]
            contrast_state = "no_exist"
            inv_location = "sii"
            diffs = []
            res.append(
                {
                    "invoice": name,
                    "invoice_id": False,
                    "csv": csv,
                    "invoice_location": inv_location,
                    "sii_match_difference_ids": diffs,
                    "sii_match_state": match_state,
                    "sii_contrast_state": contrast_state,
                }
            )
        return res, invoices_list

    def _get_not_in_sii_invoices(self, invoices):
        self.ensure_one()
        start_date = fields.Date.from_string(
            "%s-%s-01" % (str(self.fiscalyear), self.period_type)
        )
        date_from = start_date
        date_to = start_date + relativedelta(months=1)
        res = []
        inv_type = (
            ["out_invoice", "out_refund"]
            if self.invoice_type == "out"
            else ["in_invoice", "in_refund"]
        )
        invoice_ids = self.env["account.move"].search(
            [
                ("date", ">=", date_from),
                ("date", "<", date_to),
                ("company_id", "=", self.company_id.id),
                ("id", "not in", list(invoices.keys())),
                ("move_type", "in", inv_type),
            ]
        )
        for invoice in invoice_ids.filtered("sii_enabled"):
            if "out_invoice" in inv_type:
                number = invoice.name or invoice.thirdparty_number or _("Draft")
            else:
                number = invoice.ref
            res.append(
                {
                    "invoice": number,
                    "invoice_id": invoice.id,
                    "sii_contrast_state": "no_exist",
                    "invoice_location": "odoo",
                }
            )
        return res

    def _update_odoo_invoices(self, invoices):
        self.ensure_one()
        for invoice_id, values in list(invoices.items()):
            invoice = self.env["account.move"].browse([invoice_id])
            invoice.sii_match_difference_ids.unlink()
            invoice.write(values)
        return []

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
            (0, 0, i)
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
            serv = (
                self.env["account.move"]
                .search([("company_id", "in", [self.company_id.id, False])], limit=1)
                ._connect_aeat(mapping_key)
            )
            header = sii_match_report._get_aeat_header()
            match_vals = {}
            summary = {}
            try:
                inv_dict = sii_match_report._get_invoice_dict()
                if sii_match_report.invoice_type == "out":
                    res = serv.ConsultaLRFacturasEmitidas(header, inv_dict)
                    res_line = res["RegistroRespuestaConsultaLRFacturasEmitidas"]
                elif sii_match_report.invoice_type == "in":
                    res = serv.ConsultaLRFacturasRecibidas(header, inv_dict)
                    res_line = res["RegistroRespuestaConsultaLRFacturasRecibidas"]
                if res_line:
                    (
                        match_vals["sii_match_result"],
                        summary,
                    ) = sii_match_report._get_match_result_values(res_line)
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
                sii_match_report.sii_match_result.mapped(
                    "sii_match_difference_ids"
                ).unlink()
                sii_match_report.sii_match_result.unlink()
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
                _("No VAT configured for the company '{}'").format(company.name)
            )
        header = {
            "IDVersionSii": SII_VERSION,
            "Titular": {
                "NombreRazon": self.company_id.name[0:120],
                "NIF": self.company_id.vat[2:],
            },
        }
        return header

    def button_calculate(self):
        for match in self:
            for queue in match.mapped("sii_match_jobs_ids"):
                if queue.state in ("pending", "enqueued", "failed"):
                    queue.sudo().unlink()
                elif queue.state == "started":
                    raise exceptions.UserError(
                        _(
                            "You can not calculate at this moment "
                            "because there is a job running"
                        )
                    )
        self._process_invoices_from_sii()
        return []

    def button_cancel(self):
        self.write({"state": "cancelled"})
        return []

    def button_recover(self):
        self.write({"state": "draft"})
        return []

    def button_confirm(self):
        self.write({"state": "done"})
        return []

    def open_result(self):
        self.ensure_one()
        tree_view = self.env.ref(
            "l10n_es_aeat_sii_match.view_l10n_es_aeat_sii_match_result_tree"
        )
        return {
            "name": _("Results"),
            "view_mode": "tree, form",
            "res_model": "l10n.es.aeat.sii.match.result",
            "views": [(tree_view and tree_view.id or False, "tree"), (False, "form")],
            "type": "ir.actions.act_window",
            "domain": [("id", "in", self.sii_match_result.ids)],
            "context": {},
        }

    def get_invoice_aeat(self):
        self._get_invoices_from_sii()


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
    invoice_id = fields.Many2one(string="Odoo invoice", comodel_name="account.move")
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
