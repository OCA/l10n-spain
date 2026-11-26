# Copyright 2026 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
from datetime import datetime, timedelta

from pytz import UTC, timezone

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class HrSiltra(models.Model):
    _name = "hr.siltra"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Fichero de SILTRA a procesar"

    name = fields.Char()
    filename = fields.Char(copy=False)
    file = fields.Binary(copy=False)
    file_date = fields.Datetime(copy=False, readonly=True)
    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("processed", "Procesado"),
            ("validated", "Validado"),
        ],
        default="draft",
        copy=False,
        tracking=True,
    )
    item_ids = fields.One2many("hr.siltra.item", inverse_name="siltra_id")
    to_review_item_ids = fields.One2many(
        "hr.siltra.item",
        domain=[("state", "=", "draft")],
        inverse_name="siltra_id",
    )
    reviewed_item_ids = fields.One2many(
        "hr.siltra.item",
        domain=[("state", "=", "validated")],
        inverse_name="siltra_id",
    )
    nac_items = fields.Integer(compute="_compute_item_counts", string="Births")
    dit_items = fields.Integer(compute="_compute_item_counts", string="Absences")
    dip_items = fields.Integer(compute="_compute_item_counts", string="Disability")
    jub_items = fields.Integer(compute="_compute_item_counts", string="Retirements")

    @api.depends("item_ids.process_type")
    def _compute_item_counts(self):
        for record in self:
            record.nac_items = len(
                record.item_ids.filtered(lambda i: i.process_type == "NAC")
            )
            record.dit_items = len(
                record.item_ids.filtered(lambda i: i.process_type == "DIT")
            )
            record.dip_items = len(
                record.item_ids.filtered(lambda i: i.process_type == "DIP")
            )
            record.jub_items = len(
                record.item_ids.filtered(lambda i: i.process_type == "JUB")
            )

    def process(self):
        for record in self.filtered(lambda r: r.state == "draft" and r.file):
            record._process_file()

    def _process_file(self):
        self.ensure_one()
        data = base64.b64decode(self.file)
        vals = {
            "mvals": [],
            "context": {},
            "file_date": False,
        }
        for line in data.decode("latin-1").splitlines():
            line_type = line[0:3]
            if hasattr(self, f"_process_{line_type}"):
                getattr(self, f"_process_{line_type}")(line, vals)
        for single_vals in vals["mvals"]:
            single_vals["data"] = (
                "<ul>"
                + ("".join(f"<li>{k}: {v}</li>" for k, v in single_vals.pop("data")))
                + "</ul>"
            )
        self.env["hr.siltra.item"].create(vals["mvals"])
        self.file_date = vals["file_date"]
        self.state = "processed"
        for item in self.item_ids.filtered(
            lambda i: i.process_type == "DIT" and i.end_date and i.start_date
        ):
            item.validate()
        if not self.item_ids.filtered(lambda i: i.state == "draft"):
            self.validate()

    def validate(self):
        if any(self.item_ids.filtered(lambda i: i.state == "draft")):
            raise UserError(
                _(
                    "Cannot validate a SILTRA file with unprocessed items. "
                    "Please process the file first."
                )
            )
        self.state = "validated"

    def _process_ETI(self, line, vals):
        vals["file_date"] = datetime.strptime(line[29:41], "%Y%m%d%H%M")
        pass

    def _process_EMP(self, line, vals):
        vals["context"]["company"] = (
            self.env["res.company.seguridad.social"]
            .search([("ss_number", "=", line[3:18])], limit=1)
            .company_id
        )

    def _process_TRA(self, line, vals):
        if vals.get("vals"):
            vals["mvals"].append(vals.pop("vals"))
        ssnid = line[3:15]
        vals["vals"] = {
            "ssnid": ssnid,
            "company_id": vals["context"]["company"].id,
            "siltra_id": self.id,
            "employee_id": self.env["hr.employee"]
            .search(
                [
                    ("ssnid", "=", ssnid),
                    ("company_id", "=", vals["context"]["company"].id),
                ],
                limit=1,
            )
            .id,
            "data": [
                ["Número de la Seguridad Social", ssnid],
                ["Identificador de persona física (IPF)", line[15:33]],
                ["Nacionalidad", line[61:64]],
            ],
        }

    def _process_AYN(self, line, vals):
        vals["vals"]["data"] += [
            ["Apellido 1", line[3:23].strip()],
            ["Apellido 2", line[23:43].strip()],
            ["Nombre", line[43:63].strip()],
        ]

    def _process_DAF(self, line, vals):
        if line[11:19] != "00000000":
            vals["vals"]["data"].append(
                [
                    "Fecha Inicio Relación Laboral",
                    datetime.strptime(line[3:11], "%Y%m%d").date().isoformat(),
                ]
            )
        if line[11:19] != "00000000":
            vals["vals"]["data"].append(
                [
                    "Fecha Extinción Relación Laboral",
                    datetime.strptime(line[11:19], "%Y%m%d").date().isoformat(),
                ]
            )

    def _process_DIT(self, line, vals):
        vals["vals"]["process_type"] = "DIT"
        vals["vals"]["data"] += [
            ["Entidad Responsable", line[3:6]],
            [
                "Fecha Inicio Incapacidad Temporal",
                datetime.strptime(line[6:14], "%Y%m%d").date().isoformat(),
            ],
            ["Recaída", "Sí" if line[14:15] == "S" else "No"],
            ["Días acumulados en el proceso", int(line[31:35])],
        ]
        if line[15:23] != "00000000":
            vals["vals"]["data"].append(
                [
                    "Fecha Proceso Inicial",
                    datetime.strptime(line[15:23], "%Y%m%d").date().isoformat(),
                ]
            )
        if line[23:31] != "00000000":
            vals["vals"]["data"].append(
                [
                    "Fecha Proceso anterior",
                    datetime.strptime(line[23:31], "%Y%m%d").date().isoformat(),
                ]
            )
        if line[35:43] != "00000000":
            vals["vals"]["data"].append(
                [
                    "Fecha Proceso IT Inexistente",
                    datetime.strptime(line[35:43], "%Y%m%d").date().isoformat(),
                ]
            )
        vals["vals"]["start_date"] = datetime.strptime(line[6:14], "%Y%m%d").date()
        if line[62:70] != "00000000":
            vals["vals"]["end_date"] = datetime.strptime(line[62:70], "%Y%m%d").date()

    def _process_IT2(self, line, vals):
        if line[3:11] != "00000000":
            end_date = datetime.strptime(line[3:11], "%Y%m%d").date().isoformat()
            vals["vals"]["data"].append(
                [
                    "Fecha siguiente revisión médica",
                    end_date,
                ]
            )
            if not vals["vals"].get("end_date"):
                vals["vals"]["end_date"] = end_date
            if not vals["vals"].get("last_date"):
                vals["vals"]["last_date"] = end_date

    def _process_CIT(self, line, vals):
        pass

    def _process_DIP(self, line, vals):
        vals["vals"]["process_type"] = "DIP"
        vals["vals"]["start_date"] = datetime.strptime(line[11:19], "%Y%m%d").date()
        if line[42:50] != "00000000":
            vals["vals"]["end_date"] = datetime.strptime(line[42:50], "%Y%m%d").date()

    def _process_JUB(self, line, vals):
        vals["vals"]["process_type"] = "JUB"
        vals["vals"]["start_date"] = datetime.strptime(line[5:13], "%Y%m%d").date()
        vals["vals"]["data"] += [
            ["Tipo de resolución", line[3]],
            ["Tipo de jubilación", line[4]],
        ]

    def _process_NAC(self, line, vals):
        vals["vals"]["process_type"] = "NAC"
        vals["vals"]["start_date"] = datetime.strptime(line[3:11], "%Y%m%d").date()

    def _process_DOP(self, line, vals):
        vals["vals"]["process_type"] = "DOP"
        vals["vals"]["start_date"] = datetime.strptime(line[17:25], "%Y%m%d").date()
        vals["vals"]["end_date"] = datetime.strptime(line[25:33], "%Y%m%d").date()
        vals["vals"]["partial_percentage"] = int(line[41:46]) / 100
        vals["vals"]["data"] += [
            ["Motivo de Solicitud", self._map_dop_reason(line[3:5])],
        ]

    def _map_dop_reason(self, code):
        return {
            "NC": "Nacimiento y cuidado del menor",
            "RE": "Riesgo durante el Embarazo",
            "RL": "Riesgo durante la Lactancia",
            "CM": "Cuidado del menor",
            "CL": "Correspondiente al cuidado del lactante",
        }.get(code, code)

    def _process_ETF(self, line, vals):
        if vals.get("vals"):
            vals["mvals"].append(vals.pop("vals"))


class HrSiltraItem(models.Model):
    _name = "hr.siltra.item"
    _description = "Línea del proceso de un fichero de SILTRA"

    siltra_id = fields.Many2one(
        "hr.siltra",
        string="Fichero de SILTRA",
        required=True,
        ondelete="cascade",
        readonly=True,
    )
    ssnid = fields.Char(string="Número de la Seguridad Social")
    company_id = fields.Many2one("res.company", string="Empresa", readonly=True)
    employee_id = fields.Many2one("hr.employee", string="Empleado")
    partial_percentage = fields.Float()
    process_type = fields.Selection(
        [
            ("DIT", "Incapacidad Temporal"),
            ("DIP", "Incapacidad Permanente"),
            ("JUB", "Jubilación"),
            ("DOP", "Otras Prestaciones"),
            ("NAC", "Nacimiento"),
        ],
        string="Tipo de proceso",
        readonly=True,
    )
    start_date = fields.Date()
    last_date = fields.Date(
        help="""Date of the last review of the process, in the case of DIT.
        This is used to set a limit date for the next validation of the process,
        as the system expects a new review at least every 30 days""",
    )
    end_date = fields.Date()
    data = fields.Html(readonly=True)
    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("validated", "Validado"),
        ],
        default="draft",
        copy=False,
        readonly=True,
    )
    leave_id = fields.Many2one("hr.leave", readonly=True)

    def validate(self):
        for record in self.filtered(
            lambda r: r.state == "draft"
            and r.employee_id
            and r.company_id.siltra_leave_type_id
        ):
            if record.process_type in ("DIT", "DOP"):
                tz = timezone(
                    record.company_id.resource_calendar_id.tz
                    or self.env.user.tz
                    or "UTC"
                )
                leave_vals = record._dit_leave_vals()
                leave = (
                    self.env["hr.leave"]
                    .with_context(leave_fast_create=True)
                    .search(
                        [
                            ("employee_id", "=", record.employee_id.id),
                            ("request_date_from", "=", leave_vals["request_date_from"]),
                            ("holiday_status_id", "=", leave_vals["holiday_status_id"]),
                            ("state", "in", ["validate"]),
                        ],
                        limit=1,
                    )
                )
                date_from_tz = (
                    tz.localize(
                        datetime.combine(
                            leave_vals["request_date_from"], datetime.min.time()
                        )
                    )
                    .astimezone(UTC)
                    .replace(tzinfo=None)
                )
                date_to_tz = (
                    tz.localize(
                        datetime.combine(
                            leave_vals["request_date_to"], datetime.max.time()
                        )
                    )
                    .astimezone(UTC)
                    .replace(tzinfo=None)
                )
                # We cancel hourly leaves that overlap with the DIT, as the DIT file
                # doesn't specify hours and the employee might have some validated
                # hourly leaves that would not be fully covered by the DIT
                conflicting_hour_leaves = (
                    self.env["hr.leave"]
                    .with_context(
                        tracking_disable=True,
                        mail_activity_automation_skip=True,
                        leave_fast_create=True,
                    )
                    .search(
                        [
                            ("date_from", "<=", date_to_tz),
                            ("date_to", ">", date_from_tz),
                            ("state", "not in", ["cancel", "refuse"]),
                            ("employee_id", "=", record.employee_id.id),
                            ("leave_type_request_unit", "in", ["hour", "half_day"]),
                            ("id", "!=", leave.id),
                        ]
                    )
                )
                conflicting_hour_leaves.action_refuse()
                conflicting_leaves = (
                    self.env["hr.leave"]
                    .with_context(
                        tracking_disable=True,
                        mail_activity_automation_skip=True,
                        leave_fast_create=True,
                    )
                    .search(
                        [
                            ("date_from", "<=", date_to_tz),
                            ("date_to", ">", date_from_tz),
                            ("state", "not in", ["cancel", "refuse"]),
                            ("employee_id", "=", record.employee_id.id),
                            ("id", "!=", leave.id),
                        ]
                    )
                )
                conflicting_leaves._split_leaves(
                    leave_vals["request_date_from"],
                    leave_vals["request_date_to"] + timedelta(days=1),
                )

                if not leave:
                    leave = (
                        self.env["hr.leave"]
                        .with_context(
                            leave_fast_create=True,
                        )
                        .create(leave_vals)
                    )
                    leave.action_approve(check_state=False)
                else:
                    leave._remove_resource_leave()
                    leave.with_context(leave_skip_state_check=True).write(leave_vals)
                    leave._create_resource_leave()
                record.leave_id = leave
            record.state = "validated"

    def _dit_leave_vals(self):
        self.ensure_one()
        end_date = self.end_date
        if not end_date and self.last_date:
            # If we don't have an end date, we set it to 30 days after
            # the last date related to the DIT. We do it this way because that is the
            # limit date for the next validation of the process
            end_date = self.last_date + timedelta(days=30)
        return {
            "name": f"Proceso de IT desde {self.start_date} ({self.ssnid})",
            "employee_id": self.employee_id.id,
            "company_id": self.company_id.id,
            "holiday_status_id": self.company_id.siltra_leave_type_id.id,
            "request_date_from": self.start_date,
            "request_date_to": end_date or self.start_date,
        }

    def view_leave(self):
        self.ensure_one()
        if not self.leave_id:
            return
        return self.leave_id.get_formview_action()
