# Copyright 2022 ForgeFlow, S.L.
# Copyright 2023 NuoBiT Solutions, S.L. - Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime

from zeep import Client, helpers as ZeepHelpers
from zeep.exceptions import Fault
from zeep.plugins import HistoryPlugin
from zeep.transports import Transport as ZeepTransport

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


MRW_API_URL = {
    "test": "https://sagec-test.mrw.es/MRWEnvio.asmx?WSDL",
    "prod": "https://sagec.mrw.es/MRWEnvio.asmx?WSDL",
}

MRW_TRACKING_API_URL = {
    "test": "https://trackingservice.mrw.es/TrackingService.svc?wsdl",
    "prod": "https://trackingservice.mrw.es/TrackingService.svc?wsdl",
}


class MRWRequest:
    """Interface between MRW SOAP API and Odoo recordset
    Abstract MRW API Operations to connect them with Odoo

    Not all the features are implemented, but could be easily extended with
    the provided API. We leave the operations empty for future.
    """

    def __init__(self, carrier):
        self.carrier = carrier
        self.api_env = "prod" if self.carrier.prod_environment else "test"
        self.client = Client(wsdl=MRW_API_URL[self.api_env])
        self.username = self.carrier.mrw_username
        self.pasword = self.carrier.mrw_password
        self.client_code = self.carrier.mrw_client_code
        self.department_code = self.carrier.mrw_department_code or ""
        self.franquicia_code = self.carrier.mrw_franquicia_code
        self._set_soapheaders()
        self.history = HistoryPlugin(maxlen=10)

    def _set_soapheaders(self):
        credentials = self.client.get_element("ns0:AuthInfo")(
            UserName=self.username,
            Password=self.pasword,
            CodigoAbonado=self.client_code,
            CodigoDepartamento=self.department_code,
            CodigoFranquicia=self.franquicia_code,
        )

        self.client.set_default_soapheaders([credentials])

    def _process_reply(self, service, request=None):
        try:
            response = service(request=request)
        except Fault as e:
            raise UserError(e)
        return response

    def _cancel_shipment(self, reference=False):
        """Cancel shipment for the given ref
        :param str reference -- shipment reference string
        :returns: bool True if success
        """
        response = self._process_reply(
            self.client.service.CancelarEnvio,
            request={"CancelaEnvio": {"NumeroEnvioOriginal": reference}},
        )
        return response

    def _send_shipping(self, picking_vals):
        """Create new shipment
        :params vals dict of needed values
        :returns dict with MRW response containing the shipping code and label
        """
        method = "TransmEnvio"
        response = self._process_reply(
            self.client.service[method], request=picking_vals
        )
        return response

    def _get_label(self, vals, international=False):
        """Get shipping label for the given ref
        :param list reference -- shipping reference list
        :returns: base64 with pdf labels
        """
        method = "EtiquetaEnvioInternacional" if international else "EtiquetaEnvio"
        label = self._process_reply(self.client.service[method], request=vals)
        return label

    def _get_tracking_states(self, vals):
        """Get just tracking states from MRW info for the given reference"""
        transport = ZeepTransport(timeout=10)
        zeep_client = Client(
            wsdl=MRW_TRACKING_API_URL[self.api_env], transport=transport
        )
        response = zeep_client.service.GetEnvios(**vals)
        return response

    def _process_mrw_tracking_response(self, response):
        def parse_date(date_str, time_str):
            input_date = False
            try:
                if date_str and len(date_str) == 8:
                    day = int(date_str[:2])
                    month = int(date_str[2:4])
                    year = int(date_str[4:])
                    input_date = datetime(year, month, day)
                    if time_str and len(time_str) == 4:
                        hour = int(time_str[:2])
                        minute = int(time_str[2:4])
                        input_date = input_date.replace(hour=hour, minute=minute)
            except Exception:
                pass
            return input_date

        json_res = ZeepHelpers.serialize_object(response, dict)

        subscribers = json_res.get("Seguimiento", {}).get("Abonado", [])
        if not subscribers:
            return False
        trackings = subscribers[0].get("SeguimientoAbonado", {}).get("Seguimiento", {})
        if not trackings:
            return False
        states = []
        for tracking in trackings:
            delivery_date = parse_date(
                tracking.get("FechaEntrega", False), tracking.get("HoraEntrega", False)
            )
            if not delivery_date:
                delivery_date = datetime.now()
            track_dict = {
                "state_code": tracking.get("Estado", False),
                "description": tracking.get("EstadoDescripcion"),
                "delivery_date": delivery_date,
            }
            states.append(track_dict)

        return states
