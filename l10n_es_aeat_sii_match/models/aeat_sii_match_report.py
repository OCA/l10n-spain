# Copyright 2018 Studio73 - Abraham Anes
# Copyright 2019 Studio73 - Pablo Fuentes
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
import json
from odoo import _, api, exceptions, fields, models
from dateutil.relativedelta import relativedelta

from odoo.modules.registry import Registry


_logger = logging.getLogger(__name__)
try:
    from odoo.addons.queue_job.job import job
    from odoo.addons.queue_job.exception import RetryableJobError
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
        help="Search invoices with the accounting date in this period.",
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
    sii_match_invoice_jobs_ids = fields.Many2many(
        comodel_name="queue.job",
        relation="sii_match_inv_jobs_rel",
        column1="sii_match_id",
        column2="job_id",
        string="Connector Invoice Update Jobs",
        copy=False,
    )

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
    def _get_aeat_odoo_invoices_by_csv(self, aeat_invoices):
        """Get AEAT matched Invoices and non matched

        Args:
            aeat_invoices (JSON): AEAT SII Invoices JSON

        Returns:
            Tuple(Dict, List(Dict)): AEAT matched Invoices, not matched Invoices
        """
        period_invoices_dict = {}
        _logger.info("Building hashmap...")
        # Build dict for better performance inside for loop checking CSV
        for invoice in self._get_odoo_period_invoices(extra_query_fields=["sii_csv"]):
            period_invoices_dict[invoice["sii_csv"]] = invoice["id"]
        matched_invoices = {}
        invoices_not_in_odoo = []
        _logger.info("Getting matched Invoices...")
        for aeat_invoice_json in aeat_invoices:
            aeat_invoice = json.loads(json.dumps(serialize_object(aeat_invoice_json)))
            csv = aeat_invoice["DatosPresentacion"]["CSV"]
            invoice_state = aeat_invoice["EstadoFactura"]["EstadoRegistro"]
            odoo_invoice_id = period_invoices_dict.get(csv, False)
            if odoo_invoice_id:
                matched_invoices[odoo_invoice_id] = aeat_invoice
            elif invoice_state != "Anulada":
                invoices_not_in_odoo.append(aeat_invoice)
        _logger.info("%d matched Invoices found." % len(matched_invoices))
        _logger.info("%d Invoices not in Odoo found." % len(invoices_not_in_odoo))
        return matched_invoices, invoices_not_in_odoo

    @api.multi
    def _get_aeat_odoo_invoices(self, aeat_invoices):
        """Get all invoices dict, SII matches and update matched Invoices

        Args:
            aeat_invoices (JSON): AEAT SII JSON

        Returns:
            Tuple(List(Dict): AEAT Invoices with contrast and matching information
        """
        queue_obj = self.env["queue.job"].sudo()
        matched_invoices, invoices_not_in_odoo = self._get_aeat_odoo_invoices_by_csv(
            aeat_invoices
        )
        aeat_invoices = []
        _logger.info("Getting AEAT Invoices dicts from matched...")
        sii_match_invoice_jobs_ids = self.sii_match_invoice_jobs_ids.ids
        for odoo_invoice_id, aeat_invoice in list(matched_invoices.items()):
            name = aeat_invoice["IDFactura"]["NumSerieFacturaEmisor"]
            csv = aeat_invoice["DatosPresentacion"]["CSV"]
            match_state = aeat_invoice["EstadoFactura"]["EstadoCuadre"]
            inv_location = "both"
            contrast_state = "correct"
            odoo_period_invoice = self._get_odoo_period_invoice(
                odoo_invoice_id, ["sii_contrast_state", "sii_content_sent"]
            )
            diffs = False
            if not odoo_period_invoice["sii_contrast_state"]:
                # If it's been contrasted before there is no need to check again
                diffs = self._get_diffs_values(odoo_period_invoice, aeat_invoice)
                if diffs:
                    contrast_state = "partially"
                values = {
                    "sii_match_return": json.dumps(str(aeat_invoice), indent=4),
                    "sii_match_state": match_state,
                    "sii_contrast_state": contrast_state,
                    "sii_match_difference_ids": diffs,
                }
                new_delay = self.with_delay(max_retries=5).update_invoice(
                    odoo_invoice_id, values
                )
                if new_delay:
                    jb = queue_obj.search([("uuid", "=", new_delay.uuid)], limit=1)
                    sii_match_invoice_jobs_ids.append(jb.id)
            aeat_invoices.append(
                {
                    "invoice": name,
                    "invoice_id": odoo_invoice_id,
                    "csv": csv,
                    "invoice_location": inv_location,
                    "sii_match_difference_ids": diffs,
                    "sii_match_state": match_state,
                    "sii_contrast_state": contrast_state,
                }
            )
        self.write(
            {
                "sii_match_invoice_jobs_ids": [
                    (6, 0, list(set(sii_match_invoice_jobs_ids)))
                ]
            }
        )
        _logger.info("Getting AEAT Invoices dicts from non matched...")
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

        return aeat_invoices

    def _check_invoice_jobs_finished(self):
        self.ensure_one()
        for job in self.sii_match_invoice_jobs_ids:
            if job.state in ["pending", "enqueued", "started", "failed"]:
                raise RetryableJobError(
                    _(
                        "You can not calculate at this moment "
                        "because there is a job (%s) not correctly processed"
                    )
                    % (job.uuid)
                )

    @job(
        default_channel="root.aeat_sii_match",
        retry_pattern={1: 60 * 60, 2: 2 * 60 * 60},
    )
    @api.multi
    def aeat_sii_match_last_step(self, summary):
        """Get Odoo Invoices not sent to AEAT SII service and update Wizard information
        with summary report.

        Args:
            summary (Dict): Summary report
        """
        self.ensure_one()
        self._check_invoice_jobs_finished()
        match_vals = {}
        inv_type = (
            ["out_invoice", "out_refund"]
            if self.invoice_type == "out"
            else ["in_invoice", "in_refund"]
        )
        non_matched_invoices = self.env["account.invoice"].browse(
            [
                inv.get("id")
                for inv in self._get_odoo_period_invoices(non_matched_invoices=True)
            ]
        )
        sii_match_result = []
        for invoice in non_matched_invoices:
            if invoice.sii_enabled:
                if "out_invoice" in inv_type:
                    number = invoice.number or _("Draft")
                else:
                    number = invoice.reference
                values = {
                    "invoice": number,
                    "invoice_id": invoice.id,
                    "sii_contrast_state": "no_exist",
                    "invoice_location": "odoo",
                }
                sii_match_result.append((0, 0, values))
                self._update_summary([values], summary)
        match_vals.update(summary)
        match_vals["sii_match_result"] = sii_match_result
        match_vals["state"] = "calculated"
        match_vals["calculate_date"] = fields.Datetime.now()
        self.write(match_vals)
        return True

    @api.multi
    def _get_diffs_values(self, odoo_invoice, aeat_invoice):
        self.ensure_one()
        if odoo_invoice["sii_content_sent"]:
            if self.invoice_type == "out":
                odoo_dict_key = "FacturaExpedida"
                aeat_dict_key = "DatosFacturaEmitida"
            else:
                odoo_dict_key = "FacturaRecibida"
                aeat_dict_key = "DatosFacturaRecibida"
            return self.env["account.invoice"]._get_diffs(
                json.loads(odoo_invoice["sii_content_sent"])[odoo_dict_key],
                aeat_invoice[aeat_dict_key],
            )
        else:
            return False

    @api.multi
    def _get_odoo_period_invoice(self, odoo_invoice_id, query_fields):
        self.ensure_one()
        where_clause = ["id = %s"]
        params = [odoo_invoice_id]
        query = """
            SELECT
                {}
            FROM
                account_invoice
            WHERE
                {}
        """.format(
            ", ".join(["id"] + query_fields), " AND ".join(where_clause)
        )
        self.env.cr.execute(query, tuple(params))
        res = self.env.cr.dictfetchall()
        return res and 1 == len(res) and res[0] or False

    @api.multi
    def _get_odoo_period_invoices(
        self, extra_query_fields=None, non_matched_invoices=False
    ):
        """Get Odoo Invoices from set period.

        The resquest to the Database is made always with a new Cursor.

        Args:
            extra_query_fields (optional) (List(str)): Extra query fields
            non_matched_invoices (optional) (bool): Search for non matched Invoices

        Returns:
            Dict: Odoo Invoices Dict with desired fields
        """
        _logger.info("Getting Odoo Period Invoices...")
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
        query_fields = ["id"]
        if extra_query_fields:
            query_fields += extra_query_fields
        where_clause = [
            "date >= %s",
            "date < %s",
            "type IN %s",
            "state <> 'draft'",
            "company_id = %s",
        ]
        params = [
            date_from,
            date_to,
            tuple(inv_types),
            self.company_id.id,
        ]
        if non_matched_invoices:
            where_clause.append(
                "(sii_contrast_state IS NULL OR "
                "sii_contrast_state NOT IN ('correct', 'partially'))"
            )
        query = """
            SELECT
                {}
            FROM
                account_invoice
            WHERE
                {}
            ORDER BY
                id
        """.format(
            ", ".join(query_fields), " AND ".join(where_clause)
        )
        self.env.cr.execute(query, tuple(params))
        return self.env.cr.dictfetchall()

    def _update_summary(self, invoices, summary):
        summary["number_records"] += len(invoices)
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

    @api.multi
    def _get_match_result_values(self, aeat_invoices, summary):
        """Parse AEAT SII response and build report summary.

        Args:
            aeat_invoices (JSON): AEAT Invoices JSON
            (RegistroRespuestaConsultaRecibidasType)
            summary (Dict): Summary report

        Returns:
            List(Tuple(0, 0, Dict)): List of record values for model
            'l10n.es.aeat.sii.match.result'
        """
        self.ensure_one()
        aeat_invoices = self._get_aeat_odoo_invoices(aeat_invoices)
        _logger.info("Updating Summary report with matched and non matched Invoices...")
        self._update_summary(aeat_invoices, summary)
        return [
            (0, 0, i)
            for i in aeat_invoices
            if (i["sii_contrast_state"] != "correct" or i["sii_match_state"] == "4")
        ]

    @job(default_channel="root.aeat_sii_match")
    @api.multi
    def get_invoice_aeat(self, last_invoice=None, summary=None):
        """
        Request all Invoices from a period to AEAT SII service and report the results.

        Args:
            last_invoice (optional) (Dict): "IDFactura" is neccesary for new requests
            summary (optional) (Dict): Report summary
        """
        self.ensure_one()
        queue_obj = self.env["queue.job"].sudo()
        if summary is None:
            summary = {
                "number_records": 0,
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
        mapping_key = "out_invoice"
        if self.invoice_type == "in":
            mapping_key = "in_invoice"
        serv = (
            self.env["account.invoice"]
            .search([("company_id", "=", self.company_id.id)], limit=1)
            ._connect_sii(mapping_key)
        )
        header = self._get_sii_header()
        match_vals = {}
        sii_match_result_values = []
        try:
            inv_dict = self._get_invoice_dict()
            if last_invoice is not None:
                inv_dict["ClavePaginacion"] = last_invoice["IDFactura"]
                last_invoice = None
            else:
                # First request, consecutive ones must always pass last invoice
                self.sii_match_result.mapped("sii_match_difference_ids").unlink()
                self.sii_match_result.unlink()
            if self.invoice_type == "out":
                _logger.info("ConsultaLRFacturasEmitidas")
                res = serv.ConsultaLRFacturasEmitidas(header, inv_dict)
                res_line = "RegistroRespuestaConsultaLRFacturasEmitidas"
            elif self.invoice_type == "in":
                _logger.info("ConsultaLRFacturasRecibidas")
                res = serv.ConsultaLRFacturasRecibidas(header, inv_dict)
                res_line = "RegistroRespuestaConsultaLRFacturasRecibidas"
            if res and res["IndicadorPaginacion"] == "S" and 0 < len(res[res_line]):
                # Get before match results to be able to free up some memory
                last_invoice = (
                    json.loads(json.dumps(serialize_object(res[res_line][-1])))
                )
            if res and 0 < len(res[res_line]):
                sii_match_result_values = self._get_match_result_values(
                    res[res_line], summary
                )
                _logger.info("Updating SII Match Result with non correct Invoices...")
                self.sii_match_result = sii_match_result_values
                res = None  # Free memory
                sii_match_result_values = None  # Free memory
            if last_invoice is None:
                # No more requests to be done, wait for the Invoice jobs to finish
                # to be able to obtain Invoices not matched
                new_delay = (
                    self.with_context(company_id=self.company_id.id)
                    .with_delay(
                        eta=False,
                        max_retries=10,
                    )
                    .aeat_sii_match_last_step(summary)
                )
                if new_delay:
                    jb = queue_obj.search([("uuid", "=", new_delay.uuid)], limit=1)
                    self.sii_match_jobs_ids |= jb
            else:
                new_delay = (
                    self.with_context(company_id=self.company_id.id)
                    .with_delay(
                        eta=False,
                        max_retries=1,
                    )
                    .get_invoice_aeat(
                        last_invoice=last_invoice,
                        summary=summary,
                    )
                )
                if new_delay:
                    jb = queue_obj.search([("uuid", "=", new_delay.uuid)], limit=1)
                    self.sii_match_jobs_ids |= jb
        except Exception as e:
            _logger.exception(e)
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
        queue_obj = self.env["queue.job"].sudo()
        for match_report in self.filtered(
            lambda r: r.state in ["draft", "error", "calculated"]
        ):
            jobs = match_report.sii_match_jobs_ids
            jobs |= match_report.sii_match_invoice_jobs_ids
            for job in jobs:
                if job.state in ["pending", "enqueued", "started"]:
                    raise exceptions.Warning(
                        _(
                            "You can not calculate at this moment "
                            "because there is a job (%s) pending"
                        )
                        % (job.uuid)
                    )
            match_report.sii_match_invoice_jobs_ids.unlink()
            company = match_report.company_id
            new_delay = (
                match_report.sudo()
                .with_context(company_id=company.id)
                .with_delay(
                    eta=False,
                    max_retries=1,
                )
                .get_invoice_aeat()
            )
            if new_delay:
                jb = queue_obj.search([("uuid", "=", new_delay.uuid)], limit=1)
                match_report.sudo().sii_match_jobs_ids |= jb
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

    @job(default_channel="root.aeat_sii_match")
    def update_invoice(self, odoo_invoice_id, values):
        """Update Odoo Invoices with the contrasted information from AEAT service."""
        self.env["account.invoice"].browse(odoo_invoice_id).with_context(
            recompute=False
        ).write(values)


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
