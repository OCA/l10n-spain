# Copyright 2018 Studio73 - Abraham Anes
# Copyright 2019 Studio73 - Pablo Fuentes
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import json
import copy

from dateutil.relativedelta import relativedelta

from odoo import _, api, exceptions, fields, models
from odoo.modules.registry import Registry


_logger = logging.getLogger(__name__)
try:
    from odoo.addons.queue_job.job import job
except ImportError:
    _logger.debug("Can not `import queue_job`.")
    import functools

    def empty_decorator_factory(*argv, **kwargs):
        return functools.partial

    job = empty_decorator_factory

try:
    from zeep.helpers import serialize_object
except (ImportError, IOError) as err:
    _logger.debug(err)

SII_VERSION = "1.1"


class SiiMatchReport(models.Model):
    _name = "l10n.es.aeat.sii.match.report"
    _description = "AEAT SII match Report"

    def _default_company_id(self):
        company_obj = self.env["res.company"]
        return company_obj._company_default_get("l10n.es.aeat.sii.match.report")

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
        string="State",
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
        lenght=4,
        required=True,
        default=fields.Date.from_string(fields.Date.today()).year,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=_default_company_id,
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

    @api.multi
    def _process_invoices_from_sii(self):
        queue_obj = self.env["queue.job"].sudo()
        for match_report in self:
            company = match_report.company_id
            new_delay = (
                match_report.sudo()
                .with_context(company_id=company.id)
                .with_delay(
                    eta=False,
                )
                .get_invoice_aeat()
            )
            if new_delay:
                jb = queue_obj.search([("uuid", "=", new_delay.uuid)], limit=1)
                match_report.sudo().sii_match_jobs_ids |= jb

    @api.multi
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

    @api.multi
    def _get_aeat_odoo_invoices_by_csv(self, odoo_period_invoices, aeat_invoices):
        """Get AEAT matched Invoices and non matched

        Args:
            odoo_period_invoices List(Dict): Odoo Invoices ID and SII CSV
            {"id": X, "sii_csv": Y}
            aeat_invoices (JSON): AEAT SII Invoices JSON

        Returns:
            Tuple(Dict, List(Dict)): AEAT matched Invoices, not matched Invoices
        """
        matched_invoices = {}
        invoices_not_in_odoo = []
        for aeat_invoice_json in aeat_invoices:
            aeat_invoice = json.loads(json.dumps(serialize_object(aeat_invoice_json)))
            csv = aeat_invoice["DatosPresentacion"]["CSV"]
            invoice_state = aeat_invoice["EstadoFactura"]["EstadoRegistro"]
            odoo_invoice_id = False
            i = 0
            while not odoo_invoice_id and i < len(odoo_period_invoices):
                if odoo_period_invoices[i]["sii_csv"] == csv:
                    odoo_invoice_id = odoo_period_invoices[i]["id"]
                i += 1
            if odoo_invoice_id:
                matched_invoices[odoo_invoice_id] = aeat_invoice
            elif invoice_state != "Anulada":
                invoices_not_in_odoo.append(aeat_invoice)
        return matched_invoices, invoices_not_in_odoo

    @api.multi
    def _get_aeat_odoo_invoices(self, odoo_period_invoices, aeat_invoices):
        """Get all invoices dict, SII matches and update matched Invoices

        Args:
            odoo_period_invoices List(Dict): Odoo Invoices ID and SII CSV
            {"id": X, "sii_csv": Y}
            aeat_invoices (JSON): AEAT SII JSON

        Returns:
            Tuple(List(Dict), List(int), Dict): AEAT Invoices, Matched Invoice IDs,
            Invoices to update
        """
        matched_invoices, invoices_not_in_odoo = self._get_aeat_odoo_invoices_by_csv(
            odoo_period_invoices, aeat_invoices
        )
        aeat_invoices = []
        matched_invoice_ids = []
        invoices_to_update = {}
        for odoo_invoice_id, aeat_invoice in list(matched_invoices.items()):
            matched_invoice_ids.append(odoo_invoice_id)
            name = aeat_invoice["IDFactura"]["NumSerieFacturaEmisor"]
            csv = aeat_invoice["DatosPresentacion"]["CSV"]
            match_state = aeat_invoice["EstadoFactura"]["EstadoCuadre"]
            inv_location = "both"
            contrast_state = "correct"
            odoo_invoice = self.env["account.invoice"].browse(odoo_invoice_id)
            diffs = odoo_invoice._get_diffs_values(aeat_invoice)
            if diffs:
                contrast_state = "partially"
            values = {
                "sii_match_return": json.dumps(str(aeat_invoice), indent=4),
                "sii_match_state": match_state,
                "sii_contrast_state": contrast_state,
                "sii_match_difference_ids": copy.deepcopy(diffs),
            }
            invoices_to_update[odoo_invoice_id] = values
            aeat_invoices.append(
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
        for aeat_invoice in invoices_not_in_odoo:
            name = aeat_invoice["IDFactura"]["NumSerieFacturaEmisor"]
            csv = aeat_invoice["DatosPresentacion"]["CSV"]
            match_state = aeat_invoice["EstadoFactura"]["EstadoCuadre"]
            contrast_state = "no_exist"
            inv_location = "sii"
            diffs = []
            aeat_invoices.append(
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
        
        return aeat_invoices, matched_invoice_ids, invoices_to_update

    @api.multi
    def _get_not_in_sii_invoices(self, odoo_period_invoices, matched_invoice_ids):
        """Get Odoo Invoices not sent to AEAT SII service.

        Args:
            odoo_period_invoices List(Dict): Odoo Invoices ID and SII CSV
            {"id": X, "sii_csv": Y}
            matched_invoice_ids (List(int)): Matched Invoices IDs

        Returns:
            List(Dict): Invoices not in SII
        """
        self.ensure_one()
        res = []
        inv_type = (
            ["out_invoice", "out_refund"]
            if self.invoice_type == "out"
            else ["in_invoice", "in_refund"]
        )
        invoices_not_in_sii = []
        for invoice in odoo_period_invoices:
            if invoice["id"] not in matched_invoice_ids:
                invoices_not_in_sii.append(invoice)
        for invoice in invoices_not_in_sii:
            if not invoice["sii_enabled"]:
                continue
            if "out_invoice" in inv_type:
                number = invoice["number"] or _("Draft")
            else:
                number = invoice["reference"]
            res.append(
                {
                    "invoice": number,
                    "invoice_id": invoice["id"],
                    "sii_contrast_state": "no_exist",
                    "invoice_location": "odoo",
                }
            )
        return res

    @api.multi
    def _get_odoo_period_invoices(self):
        """Get Odoo Invoices from set period

        Returns:
            List(Dict): Odoo Invoices ID and SII CSV {"id": X, "sii_csv": Y}
        """
        self.ensure_one()
        start_date = fields.Date.from_string(
            "%s-%s-01" % (str(self.fiscalyear), self.period_type)
        )
        date_from = fields.Date.to_string(start_date)
        date_to = fields.Date.to_string(start_date + relativedelta(months=1))
        inv_types = (
            ["out_invoice", "out_refund"]
            if self.invoice_type == "out"
            else ["in_invoice", "in_refund"]
        )
        return self.env["account.invoice"].search_read(
            domain=[
                ("date_invoice", ">=", date_from),
                ("date_invoice", "<", date_to),
                ("type", "in", inv_types),
                ("state", "!=", "draft"),
            ],
            fields=["id", "sii_csv", "sii_enabled", "number", "reference"],
            order="id DESC",
        )

    @api.model
    def _build_summary(self, invoices):
        summary = {
            "number_records": len(invoices),
            "number_records_both": 0,
            "number_records_sii": 0,
            "number_records_odoo": 0,
            "number_records_correct": 0,
            "number_records_no_exist": 0,
            "number_records_partially": 0,
            "number_records_no_test": 0,
            "number_records_in_process": 0,
            "number_records_not_contrasted": 0,
            "number_records_partially_contrasted": 0,
            "number_records_contrasted": 0,
        }
        for i in invoices:
            if i["invoice_location"] == "both":
                summary["number_records_both"] += 1
            elif i["invoice_location"] == "sii":
                summary["number_records_sii"] += 1
            elif i["invoice_location"] == "odoo":
                summary["number_records_odoo"] += 1

            if i["sii_contrast_state"] == "correct":
                summary["number_records_correct"] += 1
            elif i["sii_contrast_state"] == "no_exist":
                summary["number_records_no_exist"] += 1
            elif i["sii_contrast_state"] == "partially":
                summary["number_records_partially"] += 1

            if i.get("sii_match_state", False) and i["sii_match_state"] == "1":
                summary["number_records_no_test"] += 1
            elif i.get("sii_match_state", False) and i["sii_match_state"] == "2":
                summary["number_records_in_process"] += 1
            elif i.get("sii_match_state", False) and i["sii_match_state"] == "3":
                summary["number_records_not_contrasted"] += 1
            elif i.get("sii_match_state", False) and i["sii_match_state"] == "4":
                summary["number_records_partially_contrasted"] += 1
            elif i.get("sii_match_state", False) and i["sii_match_state"] == "5":
                summary["number_records_contrasted"] += 1
        return summary

    @api.multi
    def _get_match_result_values(self, aeat_invoices):
        """Parse AEAT SII response and build report summary.

        Args:
            aeat_invoices (JSON): AEAT Invoices JSON
            (RegistroRespuestaConsultaRecibidasType)

        Returns:
            Tuple(List(Dict), Dict): List of record values for model
            'l10n.es.aeat.sii.match.result', Summary
        """
        self.ensure_one()
        odoo_period_invoices = self._get_odoo_period_invoices()
        aeat_invoices, matched_invoice_ids, invoices_to_update = (
            self._get_aeat_odoo_invoices(odoo_period_invoices, aeat_invoices))
        self.with_delay().update_invoices(invoices_to_update)
        invoices_not_in_sii = self._get_not_in_sii_invoices(
            odoo_period_invoices, matched_invoice_ids
        )
        invoices = aeat_invoices + invoices_not_in_sii
        summary = self._build_summary(invoices)
        sii_match_result_values = [
            (0, 0, i)
            for i in invoices
            if (i["sii_contrast_state"] != "correct" or i["sii_match_state"] == "4")
        ]
        return sii_match_result_values, summary

    @api.multi
    def _get_invoices_from_sii(self):
        """
        Request all Invoices from a period to AEAT SII service and report the results.
        """
        for sii_match_report in self.filtered(
            lambda r: r.state in ["draft", "error", "calculated"]
        ):
            mapping_key = "out_invoice"
            if sii_match_report.invoice_type == "in":
                mapping_key = "in_invoice"
            serv = (
                self.env["account.invoice"]
                .search([], limit=1)
                ._connect_sii(mapping_key)
            )
            header = sii_match_report._get_sii_header()
            match_vals = {}
            summary = {}
            aeat_invoices = []
            sii_match_result_values = []
            try:
                # First request, maximum records retrieved 10000
                should_make_new_request = True
                pages = 1
                last_invoice = False
                while should_make_new_request:
                    inv_dict = sii_match_report._get_invoice_dict()
                    if pages > 1 and last_invoice:
                        inv_dict["ClavePaginacion"] = last_invoice["IDFactura"]
                    if sii_match_report.invoice_type == "out":
                        res = serv.ConsultaLRFacturasEmitidas(header, inv_dict)
                        res_line = res["RegistroRespuestaConsultaLRFacturasEmitidas"]
                    elif sii_match_report.invoice_type == "in":
                        res = serv.ConsultaLRFacturasRecibidas(header, inv_dict)
                        res_line = res["RegistroRespuestaConsultaLRFacturasRecibidas"]
                    if res_line:
                        aeat_invoices += res_line
                        last_invoice = res_line[-1]
                    else:
                        last_invoice = False
                    should_make_new_request = res["IndicadorPaginacion"] == "S"
                    if should_make_new_request:
                        pages += 1
                if aeat_invoices:
                    (
                        sii_match_result_values,
                        summary,
                    ) = sii_match_report._get_match_result_values(aeat_invoices)
                match_vals.update(
                    {
                        "sii_match_result": sii_match_result_values,
                    }
                )
                match_vals.update(summary)
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
                match_vals.update(
                    {
                        "state": "error",
                    }
                )
                sii_match_report.write(match_vals)
                new_cr.commit()
                new_cr.close()
                raise

    @api.multi
    def _get_sii_header(self):
        """Builds SII send header

        :return Dict with header data depending on cancellation
        """
        self.ensure_one()
        company = self.company_id
        if not company.vat:
            raise exceptions.Warning(
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

    @api.multi
    def button_calculate(self):
        for match in self:
            for queue in match.mapped("sii_match_jobs_ids"):
                if queue.state in ("pending", "enqueued", "failed"):
                    queue.sudo().unlink()
                elif queue.state == "started":
                    raise exceptions.Warning(
                        _(
                            "You can not calculate at this moment "
                            "because there is a job running"
                        )
                    )
        self._process_invoices_from_sii()
        return []

    @api.multi
    def button_cancel(self):
        self.write({"state": "cancelled"})
        return []

    @api.multi
    def button_recover(self):
        self.write({"state": "draft"})
        return []

    @api.multi
    def button_confirm(self):
        self.write({"state": "done"})
        return []

    @api.multi
    def open_result(self):
        self.ensure_one()
        tree_view = self.env.ref(
            "l10n_es_aeat_sii_match.view_l10n_es_aeat_sii_match_result_tree"
        )
        return {
            "name": _("Results"),
            "view_type": "form",
            "view_mode": "tree, form",
            "res_model": "l10n.es.aeat.sii.match.result",
            "views": [(tree_view and tree_view.id or False, "tree"), (False, "form")],
            "type": "ir.actions.act_window",
            "domain": [("id", "in", self.sii_match_result.ids)],
            "context": {},
        }

    @job(default_channel="root.invoice_validate_sii")
    @api.multi
    def get_invoice_aeat(self):
        self._get_invoices_from_sii()

    @job(default_channel="root.invoice_validate_sii")
    @api.multi
    def update_invoices(self, invoices_to_update):
        for invoice_id, values in invoices_to_update.items():
            invoice = self.env["account.invoice"].browse(invoice_id)
            if invoice.sii_match_state != values["sii_match_state"] or invoice.sii_contrast_state != values["sii_contrast_state"]:
                invoice.sii_match_difference_ids.unlink()
                invoice.write(values)


class SiiMatchResult(models.Model):
    _name = "l10n.es.aeat.sii.match.result"
    _description = "AEAT SII Match - Result"
    _order = "invoice asc"

    @api.model
    def _get_selection_sii_match_state(self):
        return self.env["account.invoice"].fields_get(allfields=["sii_match_state"])[
            "sii_match_state"
        ]["selection"]

    report_id = fields.Many2one(
        comodel_name="l10n.es.aeat.sii.match.report",
        string="AEAT SII Match Report ID",
        ondelete="cascade",
    )
    invoice = fields.Char(string="Invoice")
    invoice_id = fields.Many2one(string="Odoo invoice", comodel_name="account.invoice")
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
