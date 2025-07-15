# Copyright 2025 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import datetime
import json
import logging

from requests import Session

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from zeep import Client, Settings
    from zeep.plugins import HistoryPlugin
    from zeep.transports import Transport
except (ImportError, IOError) as err:
    _logger.debug(err)


VERIFACTU_SEND_STATES = [
    ("not_sent", "Not sent"),
    ("correct", "Sent and Correct"),
    ("incorrect", "Sent and Incorrect"),
    ("accepted_with_errors", "Sent and accepted with errors"),
]

VERIFACTU_STATE_MAPPING = {
    "Correcto": "correct",
    "Incorrecto": "incorrect",
    "AceptadoConErrores": "accepted_with_errors",
}


class VerifactuSendQueue(models.Model):
    _name = "verifactu.send.queue"
    _description = "Verifactu Send Queue"
    _order = "id desc"

    verifactu_invoice_id = fields.Many2one(
        "verifactu.invoice",
        string="VeriFactu Invoice Entry",
        index=True,
        required=True,
    )
    send_state = fields.Selection(
        selection=VERIFACTU_SEND_STATES,
        string="Verifactu send state",
        compute="_compute_send_state",
        default="not_sent",
        readonly=True,
        store=True,
        copy=False,
        help="Indicates the state of this document in relation with the "
        "presentation to Verifactu.",
    )
    send_attempt = fields.Integer(
        default=0, help="Number of attempts to send this document."
    )
    correction = fields.Boolean(
        help="True if a correction has been made to the document, and it must be resent."
    )
    company_id = fields.Many2one("res.company", required=True)
    response_line_ids = fields.One2many(
        "verifactu.send.response.line",
        "send_queue_id",
        string="Responses",
        help="Responses from Verifactu after sending the documents.",
    )
    last_error_code = fields.Char(compute="_compute_last_error_code", store=True)

    @api.depends("response_line_ids", "response_line_ids.send_state")
    def _compute_send_state(self):
        for rec in self:
            rec.send_state = "not_sent"
            last_response = rec.response_line_ids and rec.response_line_ids[0]
            if last_response:
                rec.send_state = last_response.send_state

    @api.depends("response_line_ids", "response_line_ids.error_code")
    def _compute_last_error_code(self):
        """Compute the last error code from the response lines."""
        for rec in self:
            if rec.response_line_ids:
                rec.last_error_code = rec.response_line_ids[0].error_code
            else:
                rec.last_error_code = ""

    @api.model
    def _cron_send_documents_to_verifactu(self):
        for company in self.env["res.company"].search(
            [("verifactu_enabled", "=", True)]
        ):
            # Look for documents where we have to send as an incident
            self.env.cr.execute(
                """
                SELECT id FROM verifactu_send_queue AS vsq
                WHERE (
                    vsq.send_state = 'not_sent'
                    OR
                    (vsq.send_state IN ('incorrect', 'accepted_with_errors')
                     AND vsq.correction = TRUE)
                    OR
                    (vsq.send_state = 'accepted_with_errors'
                      AND vsq.last_error_code = '2004')
                )
                AND vsq.company_id = %s
                ORDER BY id
                FOR UPDATE NOWAIT
                """,
                [company.id],  # Always use a list or tuple here
            )
            records_to_send = self.browse(r[0] for r in self.env.cr.fetchall())
            send_date = fields.Datetime.now()
            threshold_time = send_date - datetime.timedelta(seconds=240)
            outdated_records = records_to_send.filtered(
                lambda r: r.verifactu_invoice_id.document_id.verifactu_registration_date
                < threshold_time
            )
            current_records = records_to_send - outdated_records
            outdated_records.with_context(
                verifactu_incident=True
            )._send_documents_to_verifactu()
            current_records._send_documents_to_verifactu()
        return True

    def _get_verifactu_aeat_header(self):
        """Builds VERIFACTU send header

        :param tipo_comunicacion String 'A0': new reg, 'A1': modification
        :param cancellation Bool True when the communitacion es for document
            cancellation
        :return Dict with header data depending on cancellation
        """
        # todo: implementar RemisionVoluntaria
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
                _("Please, configure the Veri*FACTU certificates for your company")
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

    def _process_response_line_doc_vals(self, res, linea, header):
        estado_registro = linea["EstadoRegistro"]
        doc_vals = {
            "aeat_header_sent": json.dumps(header, indent=4),
        }
        if estado_registro == "Correcto":
            doc_vals.update(
                {
                    "aeat_state": "sent",
                    "verifactu_csv": res["CSV"],
                    "aeat_send_failed": False,
                }
            )
        elif estado_registro == "AceptadoConErrores":
            doc_vals.update(
                {
                    "aeat_state": "sent_w_errors",
                    "verifactu_csv": res["CSV"],
                    "aeat_send_failed": True,
                }
            )
        else:
            doc_vals["aeat_send_failed"] = True
        doc_vals["verifactu_return"] = linea
        send_error = False
        if linea.get("CodigoErrorRegistro"):
            send_error = "{} | {}".format(
                str(linea["CodigoErrorRegistro"]),
                str(linea["DescripcionErrorRegistro"]),
            )
        doc_vals["aeat_send_error"] = send_error
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
            if rec.verifactu_invoice_id and rec.verifactu_invoice_id.document_id:
                inv_dict = (
                    rec.verifactu_invoice_id.document_id._get_verifactu_invoice_dict()
                )
                registro_factura_list.append(inv_dict)
        try:
            serv = rec._connect_verifactu()
            res = serv.RegFactuSistemaFacturacion(header, registro_factura_list)
        except Exception as e:
            res = _("Error when trying to connect to Veri*FACTU: {}").format(e)
            create_exception = True
        response_name = ""
        response = (
            self.env["verifactu.send.response"]
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
            if not response.datetime:
                response.datetime = fields.Datetime.now()
            response.create_activity_on_exception()
        else:
            response.complete_open_activity_on_exception()

        create_response_activity = False
        respuestaLineas = "RespuestaLinea" in res and res["RespuestaLinea"] or []
        for linea in respuestaLineas:
            invoice_num = linea["IDFactura"]["NumSerieFactura"]
            invoice = self.env["account.move"].search(
                [("name", "=", invoice_num), ("company_id", "=", rec.company_id.id)],
                limit=1,
            )
            # Find the verifactu.invoice entry for this document
            verifactu_invoice = self.env["verifactu.invoice"].search(
                [("document_id", "=", f"account.move,{invoice.id}")],
                limit=1,
            )
            send_queue = self.env["verifactu.send.queue"].search(
                [("verifactu_invoice_id", "=", verifactu_invoice.id)], limit=1
            )
            send_queue.correction = False
            estado_registro = linea["EstadoRegistro"]
            self.env["verifactu.send.response.line"].sudo().create(
                {
                    "send_queue_id": send_queue.id,
                    "response": linea,
                    "send_response_id": response.id,
                    "send_state": VERIFACTU_STATE_MAPPING[estado_registro],
                    "error_code": "CodigoErrorRegistro" in linea
                    and str(linea["CodigoErrorRegistro"])
                    or "",
                }
            )
            doc_vals = self._process_response_line_doc_vals(res, linea, header)
            if (
                send_queue.verifactu_invoice_id
                and send_queue.verifactu_invoice_id.document_id
            ):
                send_queue.verifactu_invoice_id.document_id.write(doc_vals)
            send_state = VERIFACTU_STATE_MAPPING.get(linea["EstadoRegistro"], "")
            if send_state != "correct":
                create_response_activity = True
        updated_response_name = _("Verifactu sending")
        if create_exception:
            updated_response_name = _("Connection error with Verifactu")
        elif create_response_activity:
            updated_response_name = _("Incorrect invoices sent to Verifactu")
        response.name = updated_response_name
        if create_response_activity:
            response.create_send_response_activity()
        return True
