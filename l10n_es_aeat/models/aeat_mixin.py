# Copyright 2021 Tecnativa - João Marques
# Copyright 2022 ForgeFlow - Lois Rilo
# Copyright 2011-2023 Tecnativa - Pedro M. Baeza
# Copyright 2023 Aures Tic - Almudena de la Puente <almudena@aurestic.es>
# Copyright 2023-2024 Aures Tic - Jose Zambudio <jose@aurestic.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from requests import Session

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from zeep import Client
    from zeep.plugins import HistoryPlugin
    from zeep.transports import Transport
except (ImportError, IOError) as err:
    _logger.debug(err)

AEAT_DATE_FORMAT = "%d-%m-%Y"
AEAT_STATES = [
    ("not_sent", "Not sent"),
    ("sent", "Sent"),
    ("sent_w_errors", "Accepted with errors"),
]


def round_by_keys(elem, search_keys, prec=2):
    """This uses ``round`` method directly as if has been tested that Odoo's
    ``float_round`` still returns incorrect amounts for certain values. Try
    3 units x 3,77 €/unit with 10% tax and you will be hit by the error
    (on regular x86 architectures)."""
    if isinstance(elem, dict):
        for key, value in elem.items():
            if key in search_keys:
                elem[key] = round(elem[key], prec)
            else:
                round_by_keys(value, search_keys)
    elif isinstance(elem, list):
        for value in elem:
            round_by_keys(value, search_keys)


class AeatMixin(models.AbstractModel):
    _name = "aeat.mixin"
    _description = "Aeat Mixin"

    aeat_state = fields.Selection(
        selection=AEAT_STATES,
        string="AEAT send state",
        default="not_sent",
        readonly=True,
        copy=False,
        help="Indicates the state of this document in relation with the "
        "presentation at the AEAT",
    )
    aeat_send_error = fields.Text(
        string="AEAT Send Error",
        readonly=True,
        copy=False,
    )
    aeat_send_failed = fields.Boolean(
        string="SII send failed",
        copy=False,
        help="Indicates that the last attempt to communicate this document to "
        "the SII has failed. See SII return for details",
    )
    aeat_header_sent = fields.Text(
        string="AEAT last header sent",
        copy=False,
        readonly=True,
    )
    aeat_content_sent = fields.Text(
        string="AEAT last content sent",
        copy=False,
        readonly=True,
    )

    def _get_document_date(self):
        raise NotImplementedError()

    def _get_document_serial_number(self):
        raise NotImplementedError()

    def _aeat_get_partner(self):
        raise NotImplementedError()

    def _get_document_fiscal_date(self):
        raise NotImplementedError()

    def _get_document_fiscal_year(self):
        return fields.Date.to_date(self._get_document_fiscal_date()).year

    def _change_date_format(self, date):
        datetimeobject = fields.Date.to_date(date)
        new_date = datetimeobject.strftime(AEAT_DATE_FORMAT)
        return new_date

    def _get_document_period(self):
        return "%02d" % fields.Date.to_date(self._get_document_fiscal_date()).month

    def _is_aeat_simplified_invoice(self):
        """Inheritable method to allow control when an
        invoice are simplified or normal"""
        return self._aeat_get_partner().aeat_simplified_invoice

    def _get_document_amount_total(self):
        raise NotImplementedError()

    def _get_mapping_key(self):
        raise NotImplementedError()

    def _get_aeat_invoice_dict(self):
        raise NotImplementedError()

    @api.model
    def _get_aeat_taxes_map(self, codes, date):
        raise NotImplementedError()

    def _get_valid_document_states(self):
        raise NotImplementedError()

    def _get_aeat_header(self, tipo_comunicacion=False, cancellation=False):
        raise NotImplementedError()

    def _bind_service(self, client, port_name, address=None):
        raise NotImplementedError()

    def _connect_params_aeat(self, mapping_key):
        raise NotImplementedError()

    def _connect_aeat(self, mapping_key):
        self.ensure_one()
        public_crt, private_key = self.env["l10n.es.aeat.certificate"].get_certificates(
            company=self.company_id
        )
        params = self._connect_params_aeat(mapping_key)
        session = Session()
        session.cert = (public_crt, private_key)
        transport = Transport(session=session)
        history = HistoryPlugin()
        client = Client(wsdl=params["wsdl"], transport=transport, plugins=[history])
        return self._bind_service(client, params["port_name"], params["address"])

    def _get_aeat_country_code(self):
        self.ensure_one()
        return self._aeat_get_partner()._parse_aeat_vat_info()[0]

    def _aeat_check_exceptions(self):
        """Inheritable method for exceptions control when sending AEAT documentss."""
        self.ensure_one()
        partner = self._aeat_get_partner()
        country_code = self._get_aeat_country_code()
        is_simplified_invoice = self._is_aeat_simplified_invoice()
        if country_code == "ES" and not partner.vat and not is_simplified_invoice:
            raise UserError(_("The partner has not a VAT configured."))
        if not self.company_id.chart_template_id:
            raise UserError(
                _("You have to select what account chart template use this" " company.")
            )
