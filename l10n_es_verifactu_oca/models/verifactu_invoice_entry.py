# Copyright 2025 ForgeFlow S.L.
# Copyright 2025 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import datetime
import json

from requests import Session
from zeep import Client, Settings
from zeep.plugins import HistoryPlugin
from zeep.transports import Transport

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import split_every

VERIFACTU_SEND_STATES = [
    ("not_sent", "Not sent"),
    ("sent", "Sent and Correct"),
    ("incorrect", "Sent and Incorrect"),
    ("sent_w_errors", "Sent and accepted with errors"),
]

VERIFACTU_STATE_MAPPING = {
    "Correcto": "sent",
    "Incorrecto": "incorrect",
    "AceptadoConErrores": "sent_w_errors",
}


class VerifactuInvoiceEntry(models.Model):
    _name = "verifactu.invoice.entry"
    _description = "VERI*FACTU invoice entry"
    _order = "id desc"
    _rec_name = "document_hash"

    verifactu_chaining_id = fields.Many2one(
        "verifactu.chaining", string="Chaining", ondelete="restrict", required=True
    )
    model = fields.Char(readonly=True, required=True)
    document_id = fields.Many2oneReference(
        string="Document", model_field="model", readonly=True, index=True, required=True
    )
    document_name = fields.Char(readonly=True)
    previous_invoice_entry_id = fields.Many2one(
        "verifactu.invoice.entry", string="Previous Invoice Entry", readonly=True
    )
    company_id = fields.Many2one(
        "res.company", string="Company", required=True, readonly=True
    )
    document_hash = fields.Char(required=True, readonly=True)
    aeat_json_data = fields.Text(
        string="AEAT JSON Data",
        help="Generated JSON data to send to AEAT",
        readonly=True,
    )
    send_state = fields.Selection(
        selection=VERIFACTU_SEND_STATES,
        compute="_compute_send_state",
        default="not_sent",
        readonly=True,
        store=True,
        copy=False,
        help="Indicates the state of this document in relation with the "
        "presentation to VERI*FACTU.",
    )
    send_attempt = fields.Integer(
        default=0, help="Number of attempts to send this document."
    )
    response_line_ids = fields.One2many(
        "verifactu.invoice.entry.response.line",
        "entry_id",
        string="Responses",
        help="Responses from VERI*FACTU after sending the documents.",
    )
    last_error_code = fields.Char(compute="_compute_last_error_code", store=True)
    previous_hash = fields.Char(
        related="previous_invoice_entry_id.document_hash",
        readonly=True,
        string="Previous Hash",
    )
    entry_type = fields.Selection(
        selection=[
            ("register", "Register"),
            ("modify", "Modify"),
            ("cancel", "Cancel"),
        ],
        default="register",
        required=True,
    )
    last_response_line_id = fields.Many2one(
        "verifactu.invoice.entry.response.line",
        string="Last Response Line",
        readonly=True,
    )

    @api.depends("response_line_ids", "response_line_ids.send_state")
    def _compute_send_state(self):
        for rec in self:
            rec.send_state = "not_sent"
            last_response = rec.last_response_line_id
            if last_response:
                rec.send_state = last_response.send_state

    @api.depends("response_line_ids", "response_line_ids.error_code")
    def _compute_last_error_code(self):
        """Compute the last error code from the response lines."""
        for rec in self:
            if rec.last_response_line_id:
                rec.last_error_code = rec.last_response_line_id.error_code
            else:
                rec.last_error_code = ""

    @property
    def document(self):
        return self.env[self.model].browse(self.document_id).exists()

    @api.model
    def _cron_send_documents_to_verifactu(self):
        batch_limit = self.env["verifactu.mixin"]._get_verifactu_batch()
        for chaining in self.env["verifactu.chaining"].search([]):
            self.env.cr.execute(
                """
                SELECT id FROM verifactu_invoice_entry AS vsq
                WHERE vsq.send_state = 'not_sent'
                AND vsq.verifactu_chaining_id = %s
                ORDER BY id
                FOR UPDATE NOWAIT
                """,
                [chaining.id],
            )
            entries_to_send_ids = [entry[0] for entry in self.env.cr.fetchall()]
            for entries_batch_ids in split_every(batch_limit, entries_to_send_ids):
                records_to_send = self.browse(entries_batch_ids)
                send_date = fields.Datetime.now()
                threshold_time = send_date - datetime.timedelta(seconds=240)
                # Look for documents where we have to send as an incident
                outdated_records = records_to_send.filtered(
                    lambda r, t=threshold_time: r.document.verifactu_registration_date
                    < t
                )
                current_records = records_to_send - outdated_records
                outdated_records.with_context(
                    verifactu_incident=True
                )._send_documents_to_verifactu()
                current_records._send_documents_to_verifactu()
        return True

    def _get_verifactu_aeat_header(self):
        """Builds VERI*FACTU send header

        :param tipo_comunicacion String 'A0': new reg, 'A1': modification
        :param cancellation Bool True when the communitacion es for document
            cancellation
        :return Dict with header data depending on cancellation
        """
        self.ensure_one()
        if not self.company_id.vat:
            raise UserError(
                _("No VAT configured for the company '{}'").format(self.company_id.name)
            )
        header = {
            "ObligadoEmision": {
                "NombreRazon": self.company_id.name[0:120],
                "NIF": self.company_id.partner_id._parse_aeat_vat_info()[2],
            },
        }
        incident = self.env.context.get("verifactu_incident", False)
        if incident:
            header.update({"RemisionVoluntaria": {"Incidencia": "S"}})
        return header

    def _bind_verifactu_service(self, client, port_name, address=None):
        self.ensure_one()
        service = client._get_service("sfVerifactu")
        port = client._get_port(service, port_name)
        address = address or port.binding_options["address"]
        return client.create_service(port.binding.name, address)

    def _connect_verifactu_params_aeat(self):
        self.ensure_one()
        agency = self.company_id.tax_agency_id
        if not agency:
            # We use spanish agency by default to keep old behavior with
            # ir.config parameters. In the future it might be good to reinforce
            # to explicitly set a tax agency in the company by raising an error
            # here.
            agency = self.env.ref("l10n_es_aeat.aeat_tax_agency_spain")
        return agency._connect_params_verifactu(self.company_id)

    def _connect_verifactu(self):
        self.ensure_one()
        public_crt, private_key = self.env["l10n.es.aeat.certificate"].get_certificates(
            company=self.company_id
        )
        if not public_crt or not private_key:
            raise UserError(
                _("Please, configure the VERI*FACTU certificates for your company")
            )
        params = self._connect_verifactu_params_aeat()
        session = Session()
        session.cert = (public_crt, private_key)
        transport = Transport(session=session)
        history = HistoryPlugin()
        settings = Settings(forbid_entities=False)
        client = Client(
            wsdl=params["wsdl"],
            transport=transport,
            plugins=[history],
            settings=settings,
        )
        return self._bind_verifactu_service(
            client, params["port_name"], params["address"]
        )

    def _process_response_line_doc_vals(
        self,
        verifactu_response=False,
        verifactu_response_line=False,
        response_line=False,
        previous_response_line=False,
        header_sent=False,
    ):
        estado_registro = verifactu_response_line["EstadoRegistro"]
        doc_vals = {
            "aeat_header_sent": json.dumps(header_sent, indent=4),
        }
        doc_vals["verifactu_return"] = verifactu_response_line
        send_error = False
        if hasattr(verifactu_response_line, "CodigoErrorRegistro"):
            send_error = "{} | {}".format(
                str(verifactu_response_line["CodigoErrorRegistro"]),
                str(verifactu_response_line["DescripcionErrorRegistro"]),
            )
            # si ya ha devuelto previamente registro duplicado, parseamos el estado
            # del registro duplicado para dejar la factura correcta o incorrecta
            if (
                verifactu_response_line["CodigoErrorRegistro"] == 3000
                and previous_response_line
            ):
                registroDuplicado = verifactu_response_line["RegistroDuplicado"]
                estado_registro = registroDuplicado["EstadoRegistroDuplicado"]
                # en duplicados devuelve Correcta en vez de Correcto...
                if estado_registro == "Correcta":
                    estado_registro = "Correcto"
                    response_line.send_state = "sent"
                elif registroDuplicado["CodigoErrorRegistro"]:
                    # en duplicados devuelve AceptadaConErrores en vez de
                    # AceptadoConErrores...
                    if estado_registro == "AceptadaConErrores":
                        estado_registro = "AceptadoConErrores"
                        response_line.send_state = "sent_w_errors"
                    send_error = "{} | {}".format(
                        str(registroDuplicado["CodigoErrorRegistro"]),
                        str(registroDuplicado["DescripcionErrorRegistro"]),
                    )
        if estado_registro == "Correcto":
            doc_vals.update(
                {
                    "verifactu_csv": verifactu_response["CSV"],
                    "aeat_send_failed": False,
                }
            )
        elif estado_registro == "AceptadoConErrores":
            doc_vals.update(
                {
                    "verifactu_csv": verifactu_response["CSV"],
                    "aeat_send_failed": True,
                }
            )
        else:
            doc_vals["aeat_send_failed"] = True
        doc_vals["aeat_send_error"] = send_error
        if response_line.document_id:
            response_line.document.write(doc_vals)
        return doc_vals

    def _send_documents_to_verifactu(self):
        if not self:
            return False
        rec = self[0]
        header = rec._get_verifactu_aeat_header()
        registro_factura_list = []
        create_exception = False
        for rec in self:
            rec.send_attempt += 1
            if rec.document:
                inv_dict = rec.document._get_verifactu_invoice_dict()
                registro_factura_list.append(inv_dict)
        try:
            serv = rec._connect_verifactu()
            res = serv.RegFactuSistemaFacturacion(header, registro_factura_list)
        except Exception:
            res = {}
            create_exception = True
        response_name = ""
        response = (
            self.env["verifactu.invoice.entry.response"]
            .sudo()
            .create(
                {
                    "header": json.dumps(header),
                    "name": response_name,
                    "invoice_data": json.dumps(registro_factura_list),
                    "response": res,
                    "verifactu_csv": "CSV" in res and res["CSV"] or _("-"),
                }
            )
        )
        response.complete_open_activity_on_exception()
        if create_exception:
            if not response.date_response:
                response.date_response = fields.Datetime.now()
            response.create_activity_on_exception()
        create_response_activity = self._create_response_lines(
            response=response, header=header, verifactu_response=res
        )
        updated_response_name = _("VERI*FACTU sending")
        if create_exception:
            updated_response_name = _("Connection error with VERI*FACTU")
        elif create_response_activity:
            updated_response_name = _("Incorrect invoices sent to VERI*FACTU")
        response.name = updated_response_name
        if create_response_activity:
            response.create_send_response_activity()
        return True

    def _create_response_lines(
        self, response=False, header=False, verifactu_response=False
    ):
        create_response_activity = False
        # the returned object doesn't have `get` method, so use this form
        verifactu_response_lines = (
            "RespuestaLinea" in verifactu_response
            and verifactu_response["RespuestaLinea"]
            or []
        )
        models = self.env["verifactu.mixin"]._get_verifactu_reference_models()
        for verifactu_response_line in verifactu_response_lines:
            invoice_num = verifactu_response_line["IDFactura"]["NumSerieFactura"]
            for model in models:
                if document := self.env[model].search(
                    [
                        ("name", "=", invoice_num),
                        ("id", "in", self.mapped("document_id")),
                    ],
                    limit=1,
                ):
                    break
            # Find the verifactu.invoice entry for this document
            verifactu_invoice_entry = document.last_verifactu_invoice_entry_id
            previous_response_line = document.last_verifactu_response_line_id
            send_state = VERIFACTU_STATE_MAPPING[
                verifactu_response_line["EstadoRegistro"]
            ]
            vals = {
                "entry_id": verifactu_invoice_entry.id,
                "model": verifactu_invoice_entry.model,
                "document_id": verifactu_invoice_entry.document_id,
                "response": verifactu_response_line,
                "entry_response_id": response.id,
                "send_state": send_state,
                "error_code": "CodigoErrorRegistro" in verifactu_response_line
                and str(verifactu_response_line["CodigoErrorRegistro"])
                or "",
            }
            response_line = (
                self.env["verifactu.invoice.entry.response.line"].sudo().create(vals)
            )
            document.last_verifactu_response_line_id = response_line
            verifactu_invoice_entry.last_response_line_id = response_line
            self._process_response_line_doc_vals(
                verifactu_response=verifactu_response,
                verifactu_response_line=verifactu_response_line,
                response_line=response_line,
                previous_response_line=previous_response_line,
                header_sent=header,
            )
            if send_state != "sent":
                create_response_activity = True
        return create_response_activity
