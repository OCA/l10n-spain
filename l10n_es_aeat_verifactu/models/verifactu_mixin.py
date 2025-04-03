# Copyright 2024 Aures TIC - Jose Zambudio <jose@aurestic.es>
# Copyright 2024 Aures TIC - Almudena de La Puente <almudena@aurestic.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import io
import json
import logging
from urllib.parse import urlencode

from requests import Session

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.modules.registry import Registry
from odoo.tools.float_utils import float_compare

from odoo.addons.l10n_es_aeat.models.aeat_mixin import round_by_keys

_logger = logging.getLogger(__name__)

try:
    import qrcode
except (ImportError, IOError) as err:
    qrcode = None
    _logger.error(err)

###########################################
# revisar los imports que no hagan falta
# cuando funcione bien el _connect_aeat sin tener que poner
# el forbid_entities, y se pueda borrar la función _connect_verifactu
# de este fichero para usar la del aeat_mixin


_logger = logging.getLogger(__name__)

try:
    from zeep import Client, Settings
    from zeep.plugins import HistoryPlugin
    from zeep.transports import Transport
except (ImportError, IOError) as err:
    _logger.debug(err)

VERIFACTU_VERSION = 1.0
VERIFACTU_DATE_FORMAT = "%d-%m-%Y"
VERIFACTU_MACRODATA_LIMIT = 100000000.0


class VerifactuMixin(models.AbstractModel):
    _name = "verifactu.mixin"
    _inherit = "aeat.mixin"
    _description = "Verifactu Mixin"

    verifactu_enabled = fields.Boolean(
        string="Enable AEAT",
        compute="_compute_verifactu_enabled",
    )
    verifactu_hash_string = fields.Char(copy=False)
    verifactu_hash = fields.Char(copy=False)
    verifactu_refund_type = fields.Selection(
        selection=[
            # ('S', 'By substitution'), - en sii no está soportado, aquí igual?
            ("I", "By differences"),
        ],
        compute="_compute_verifactu_refund_type",
        store=True,
        readonly=False,
    )
    verifactu_description = fields.Text(
        copy=False,
    )
    verifactu_macrodata = fields.Boolean(
        string="MacroData",
        help="Check to confirm that the document has an absolute amount "
        "greater o equal to 100 000 000,00 euros.",
        compute="_compute_verifactu_macrodata",
    )
    verifactu_csv = fields.Char(copy=False, readonly=True)
    verifactu_return = fields.Text(copy=False, readonly=True)
    verifactu_registration_key = fields.Many2one(
        comodel_name="aeat.verifactu.registration.keys",
        compute="_compute_verifactu_registration_key",
        store=True,
        readonly=False,
    )
    verifactu_tax_key = fields.Selection(
        string="Verifactu tax key",
        selection="_get_verifactu_tax_keys",
        compute="_compute_verifactu_tax_key",
        store=True,
        readonly=False,
    )
    verifactu_registration_key_code = fields.Char(
        compute="_compute_verifactu_registration_key_code",
        readonly=True,
        string="Verifactu Code",
    )
    verifactu_qr_url = fields.Char("URL", compute="_compute_verifactu_qr_url")
    verifactu_qr = fields.Binary(string="QR", compute="_compute_verifactu_qr")
    verifactu_previous_document_id = fields.Reference(
        string="Previous Verifactu Document",
        selection="_selection_verifactu_reference_models",
        readonly=True,
        copy=False,
    )
    verifactu_next_document_id = fields.Reference(
        string="Next Verifactu Document",
        selection="_selection_verifactu_reference_models",
        readonly=True,
        copy=False,
    )
    verifactu_send_date = fields.Datetime(index=True, copy=False)

    @api.model
    def _selection_verifactu_reference_models(self):
        # this method is used to define the models that can be used as
        # previous documents in the verifactu mixin
        # it can be inherited to add others models if needed like pos.order
        return [("account.move", "Invoice")]

    def _compute_verifactu_enabled(self):
        raise NotImplementedError

    def _compute_verifactu_macrodata(self):
        for document in self:
            document.verifactu_macrodata = (
                float_compare(
                    abs(document._get_verifactu_amount_total()),
                    VERIFACTU_MACRODATA_LIMIT,
                    precision_digits=2,
                )
                >= 0
            )

    def _compute_verifactu_qr_url(self):
        """Returns the URL to be used in the QR code. A sample URL would be (urlencoded):
        https://prewww2.aeat.es/wlpl/TIKECONT/ValidarQR?nif=89890001K&numserie=12345678%26G33&fecha=01-01-2024&importe=241.4
        """  # noqa: B950
        for record in self:
            agency = self.env.ref("l10n_es_aeat.aeat_tax_agency_spain")
            if record.company_id.verifactu_test:
                qr_base_url = agency.verifactu_qr_base_url_test_address
            else:
                qr_base_url = agency.verifactu_qr_base_url

            qr_values = record._get_verifactu_qr_values()

            # Check all values are ASCII between 32 and 126
            for value in qr_values.values():
                try:
                    str(value).encode("ascii")
                except UnicodeEncodeError as uee:
                    raise UserError(
                        _("QR URL value '{}' is not ASCII").format(value)
                    ) from uee

            # Build QR URL
            qr_url = "{}?{}".format(
                qr_base_url,
                urlencode(qr_values, encoding="utf-8"),
            )

            record.verifactu_qr_url = qr_url

    def _compute_verifactu_qr(self):
        # If qrcode module is not available, we can't generate QR codes
        if not qrcode:
            _logger.error("qrcode module is not available")
            return
        for record in self:
            if record.state != "posted" or not record.verifactu_enabled:
                record.verifactu_qr = False
                continue
            qr = qrcode.QRCode(
                border=0, error_correction=qrcode.constants.ERROR_CORRECT_M
            )
            qr.add_data(record.verifactu_qr_url)
            qr.make()
            img = qr.make_image()
            with io.BytesIO() as temp:
                img.save(temp, format="PNG")
                record.verifactu_qr = base64.b64encode(temp.getvalue())

    def _get_verifactu_qr_values(self):
        raise NotImplementedError

    @api.model
    def _get_verifactu_tax_keys(self):
        return self.env["account.fiscal.position"]._get_verifactu_tax_keys()

    def _connect_verifactu_params_aeat(self, mapping_key):
        self.ensure_one()
        agency = self.company_id.tax_agency_id
        if not agency:
            # We use spanish agency by default to keep old behavior with
            # ir.config parameters. In the future it might be good to reinforce
            # to explicitly set a tax agency in the company by raising an error
            # here.
            agency = self.env.ref("l10n_es_aeat.aeat_tax_agency_spain")
        return agency._connect_params_verifactu(mapping_key, self.company_id)

    def _get_verifactu_aeat_header(self, tipo_comunicacion=False, cancellation=False):
        """Builds VERIFACTU send header

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
        registration_date = self.verifactu_registration_date
        if (
            self.aeat_state == "sent_w_errors"
            and registration_date < fields.Datetime.now()
        ):
            header.update({"RemisionVoluntaria": {"Incidencia": "S"}})
        return header

    def _get_verifactu_invoice_dict(self):
        self.ensure_one()
        inv_dict = {}
        mapping_key = self._get_mapping_key()
        if mapping_key in ["out_invoice", "out_refund"]:
            inv_dict = self._get_verifactu_invoice_dict_out()
        else:
            raise NotImplementedError
        round_by_keys(
            inv_dict,
            [
                "BaseImponibleOimporteNoSujeto",
                "CuotaRepercutida",
                "TipoRecargoEquivalencia",
                "CuotaRecargoEquivalencia",
                "CuotaTotal",
                "ImporteTotal",
                "BaseRectificada",
                "CuotaRectificada",
            ],
        )
        return inv_dict

    def _get_verifactu_developer_dict(self):
        """
        TODO
        Datos del desarrollador del sistema informático
        """
        return {
            "NombreRazon": _("Asoc Española de Odoo"),
            "NIF": "G87846952",
            "NombreSistemaInformatico": "odoo",
            "IdSistemaInformatico": "11",
            "Version": "1.0",
            "NumeroInstalacion": "1",
            "TipoUsoPosibleSoloVerifactu": "N",
            "TipoUsoPosibleMultiOT": "S",
            "IndicadorMultiplesOT": "S",
            "IDOtro": {
                "IDType": "",
                "ID": "",
            },
        }

    def _get_verifactu_chaining_invoice_dict(self):
        raise NotImplementedError

    def _aeat_check_exceptions(self):
        """Inheritable method for exceptions control when sending veri*FACTU invoices."""
        res = super()._aeat_check_exceptions()
        if self.company_id.verifactu_enabled and not self.verifactu_enabled:
            raise UserError(_("This invoice is not veri*FACTU enabled."))
        return res

    def _change_date_format(self, date):
        datetimeobject = fields.Date.to_date(date)
        new_date = datetimeobject.strftime(VERIFACTU_DATE_FORMAT)
        return new_date

    def _get_verifactu_hash_string(self):
        raise NotImplementedError

    def _generate_verifactu_chaining(self):
        raise NotImplementedError

    def _get_verifactu_document_type(self):
        raise NotImplementedError()

    def _get_verifactu_description(self):
        raise NotImplementedError()

    def _get_verifactu_taxes_and_total(self):
        raise NotImplementedError

    def _get_verifactu_version(self):
        return VERIFACTU_VERSION

    def _get_verifactu_receiver_dict(self):
        raise NotImplementedError

    def _compute_verifactu_refund_type(self):
        self.verifactu_refund_type = False

    def _is_aeat_simplified_invoice(self):
        """Inheritable method to allow control when an
        invoice are simplified or normal"""
        partner = self._aeat_get_partner()
        return partner.aeat_simplified_invoice

    def send_verifactu(self):
        """General public method for filtering out of the starting recordset the records
        that shouldn't be sent to Verifactu:

        - Documents of companies with Verifactu not enabled (through verifactu_enabled).
        - Documents not applicable to be sent to Verifactu (through verifactu_enabled).
        - Documents in non applicable states (for example, cancelled invoices).
        - Documents already sent to Verifactu.
        - Documents with sending jobs pending to be executed.
        """
        valid_states = self._get_verifactu_valid_document_states()
        documents = self.filtered(
            lambda doc: doc.state in valid_states
            and doc.aeat_state in ["not_sent", "sent_w_errors"]
            and doc.verifactu_enabled
        )
        if documents:
            documents._process_verifactu_send()
            verifactu_send_cron = self.env.ref(
                "l10n_es_aeat_verifactu.invoice_send_to_verifactu"
            )
            self.env["ir.cron.trigger"].sudo().create(
                {"cron_id": verifactu_send_cron.id, "call_at": fields.Datetime.now()}
            )

    def _process_verifactu_send(self):
        for record in self:
            record.verifactu_send_date = fields.Datetime.now()
            record.confirm_verifactu_one_document()

    def confirm_verifactu_one_document(self):
        self.sudo()._send_document_to_verifactu()

    def _send_document_to_verifactu(self):
        for document in self.filtered(
            lambda i: i.state in self._get_verifactu_valid_document_states()
        ):
            if document.aeat_state == "not_sent":
                tipo_comunicacion = "A0"
            else:
                tipo_comunicacion = "A1"
            header = document._get_verifactu_aeat_header(tipo_comunicacion)
            doc_vals = {
                "aeat_header_sent": json.dumps(header, indent=4),
            }
            try:
                inv_dict = document._get_verifactu_invoice_dict()
            except Exception as fault:
                raise ValidationError(fault) from fault
            try:
                mapping_key = document._get_mapping_key()
                serv = document._connect_verifactu(mapping_key)
                doc_vals["aeat_content_sent"] = json.dumps(inv_dict, indent=4)
                if mapping_key in ["out_invoice", "out_refund"]:
                    res = serv.RegFactuSistemaFacturacion(header, inv_dict)
                res_line = res["RespuestaLinea"][0]
                if res["EstadoEnvio"] == "Correcto":
                    doc_vals.update(
                        {
                            "aeat_state": "sent",
                            "verifactu_csv": res["CSV"],
                            "aeat_send_failed": False,
                        }
                    )
                elif (
                    res["EstadoEnvio"] == "ParcialmenteCorrecto"
                    and res_line["EstadoRegistro"] == "AceptadoConErrores"
                ):
                    doc_vals.update(
                        {
                            "aeat_state": "sent_w_errors",
                            "verifactu_csv": res["CSV"],
                            "aeat_send_failed": True,
                        }
                    )
                else:
                    doc_vals["aeat_send_failed"] = True
                doc_vals["verifactu_return"] = res
                send_error = False
                if res_line["CodigoErrorRegistro"]:
                    send_error = "{} | {}".format(
                        str(res_line["CodigoErrorRegistro"]),
                        str(res_line["DescripcionErrorRegistro"]),
                    )
                doc_vals["aeat_send_error"] = send_error
                document.write(doc_vals)
            except Exception as fault:
                new_cr = Registry(self.env.cr.dbname).cursor()
                env = api.Environment(new_cr, self.env.uid, self.env.context)
                document = env[document._name].browse(document.id)
                doc_vals.update(
                    {
                        "aeat_send_failed": True,
                        "aeat_send_error": repr(fault)[:200],
                        "verifactu_return": repr(fault),
                        "aeat_content_sent": json.dumps(inv_dict, indent=4),
                    }
                )
                document.write(doc_vals)
                new_cr.commit()
                new_cr.close()
                raise ValidationError(fault) from fault

    def _connect_verifactu(self, mapping_key):
        # de momento no puedo el _connect_aeat del aeat_mixin porque si no pongo
        # forbid_entities en settings del Client da error de entities forbiden
        self.ensure_one()
        public_crt, private_key = self.env["l10n.es.aeat.certificate"].get_certificates(
            company=self.company_id
        )
        params = self._connect_verifactu_params_aeat(mapping_key)
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

    def _bind_verifactu_service(self, client, port_name, address=None):
        self.ensure_one()
        service = client._get_service("sfVerifactu")
        port = client._get_port(service, port_name)
        address = address or port.binding_options["address"]
        return client.create_service(port.binding.name, address)

    @api.model
    def _get_verifactu_taxes_map(self, codes, date):
        """Return the codes that correspond to verifactu map line codes.

        :param codes: List of code strings to get the mapping.
        :param date: Date to map
        :return: Recordset with the corresponding codes
        """
        map_obj = self.env["aeat.verifactu.map"].sudo().with_context(active_test=False)
        verifactu_map = map_obj.search(
            [
                "|",
                ("date_from", "<=", date),
                ("date_from", "=", False),
                "|",
                ("date_to", ">=", date),
                ("date_to", "=", False),
            ],
            limit=1,
        )
        tax_templates = verifactu_map.map_lines.filtered(
            lambda x: x.code in codes
        ).taxes
        return self.company_id.get_taxes_from_templates(tax_templates)

    @api.depends("fiscal_position_id")
    def _compute_verifactu_tax_key(self):
        for document in self:
            document.verifactu_tax_key = (
                document.fiscal_position_id.verifactu_tax_key or "01"
            )

    @api.depends("fiscal_position_id")
    def _compute_verifactu_registration_key(self):
        for document in self:
            if document.fiscal_position_id:
                key = document.fiscal_position_id.verifactu_registration_key
                if key:
                    document.verifactu_registration_key = key
            else:
                domain = [
                    ("code", "=", "01"),
                    (
                        "verifactu_tax_key",
                        "=",
                        "01",
                    ),
                ]
                verifactu_key_obj = self.env["aeat.verifactu.registration.keys"]
                document.verifactu_registration_key = verifactu_key_obj.search(
                    domain, limit=1
                )

    @api.depends("verifactu_registration_key")
    def _compute_verifactu_registration_key_code(self):
        for record in self:
            record.verifactu_registration_key_code = (
                record.verifactu_registration_key.code
            )

    def _raise_exception_verifactu(self, field_name):
        raise UserError(
            _(
                "You cannot change the %s of document"
                "already registered at Verifactu. You must cancel the "
                "document and create a new one with the correct value"
            )
            % field_name
        )

    @api.model
    def _get_verifactu_batch(self):
        try:
            return int(
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("l10n_es_aeat_verifactu.verifactu_batch", "50")
            )
        except ValueError as e:
            raise UserError(
                _(
                    "The value in l10n_es_aeat_verifactu.verifactu_batch "
                    "system parameter must be an integer. Please, check the "
                    "value of the parameter."
                )
            ) from e
